#include <bits/stdc++.h>
using namespace std;

/*
 Archipelago Relay Network Design — heuristic.

 Line graph islands 0..L, adjacent edges cost 1.
 A hired resident i creates chord (l,r), r-l<=D_i, with:
   edge cost  e = bad(C_i, l, r)  (routes on [l,r] not owned by C_i)
   setup cost = H_i + min(bad(C_i, X_i, l), bad(C_i, X_i, r))
 Demand j ships W_j from A_j to B_j; baseline path cost = |A-B|.

 A chord (l,r) (l<r) of edge cost e saves, for a demand whose interval
 fully contains [l,r], W_j * ((r-l) - e). We model "traffic over interval"
 by a coverage weight: cov[a..b] = total W over demands containing [a,b].
 We approximate the benefit of a chord by (span - e) * (traffic that would
 route through it). Hire chords with net benefit > 0, greedily, subtracting
 consumed traffic so two overlapping chords don't double count.

 Output: for each resident, "-1" or "l r".
 Always feasible (default -1).
*/

int main(){
    int L,N,M;
    scanf("%d %d %d",&L,&N,&M);
    char Sbuf[5005];
    scanf("%s",Sbuf);
    string S(Sbuf);
    vector<int> X(N), H(N), D(N);
    vector<char> C(N);
    for(int i=0;i<N;i++){
        char cb[4];
        scanf("%d %s %d %d",&X[i],cb,&H[i],&D[i]);
        C[i]=cb[0];
    }
    vector<int> A(M),B(M);
    vector<long long> W(M);
    for(int j=0;j<M;j++){
        scanf("%d %d %lld",&A[j],&B[j],&W[j]);
    }

    // prefix bad counts
    // prefBadA[k] = # routes in [1..k] with S != 'A'
    vector<int> prefBadA(L+1,0), prefBadJ(L+1,0);
    for(int k=1;k<=L;k++){
        prefBadA[k]=prefBadA[k-1]+(S[k-1]!='A'?1:0);
        prefBadJ[k]=prefBadJ[k-1]+(S[k-1]!='J'?1:0);
    }
    auto badR=[&](char c,int u,int v)->int{
        if(u>v) swap(u,v);
        if(c=='A') return prefBadA[v]-prefBadA[u];
        else       return prefBadJ[v]-prefBadJ[u];
    };

    // Demand coverage: we want, for a chord [l,r], the total W of demands
    // whose [min,max] interval fully contains [l,r].
    // Equivalent: a demand with interval [a,b] (a<b) covers chord [l,r] iff a<=l and r<=b.
    // We'll compute, over candidate chords, traffic via a 2D-ish reasoning approximated.
    //
    // To keep it tractable we use a per-position "flow" array: flow[k] = total W of
    // demands whose interval spans the unit segment between k-1 and k.
    // A chord [l,r] can capture at most min over its span of flow? No — a chord captures
    // a demand only if the demand contains the WHOLE [l,r]. The traffic eligible for
    // chord [l,r] is sum of W over demands with a<=l && b>=r.
    // We approximate eligible traffic by flowMin = min_{k in (l,r]} flow[k], which is an
    // upper bound proxy (a demand contributes to every unit segment it spans, so demands
    // containing [l,r] all contribute to every segment in (l,r], hence flowMin >= eligible,
    // but flowMin also counts demands that only partially overlap; still a useful proxy).
    //
    // For ranking we instead compute eligible traffic more accurately for chosen candidate
    // chords using sorted demands.

    // Precompute flow (segment coverage) via difference array.
    vector<long long> flow(L+2,0);
    for(int j=0;j<M;j++){
        int a=A[j],b=B[j]; if(a>b) swap(a,b);
        if(a==b) continue;
        flow[a+1]+=W[j]; // segment index k in [a+1..b] (segment between k-1,k)
        flow[b+1]-=W[j];
    }
    for(int k=1;k<=L;k++) flow[k]+=flow[k-1];
    // flow[k] for k in 1..L = traffic crossing unit segment k.

    // Sparse table on flow for range-min over (l, r] = segments l+1..r.
    int LOG=1; while((1<<LOG) <= L) LOG++;
    vector<vector<long long>> sp(LOG, vector<long long>(L+2,0));
    for(int k=1;k<=L;k++) sp[0][k]=flow[k];
    for(int j=1;j<LOG;j++)
        for(int k=1;k+(1<<j)-1<=L;k++)
            sp[j][k]=min(sp[j-1][k], sp[j-1][k+(1<<(j-1))]);
    auto rminFlow=[&](int lo,int hi)->long long{ // min over segments [lo..hi]
        if(lo>hi) return 0;
        int j=31-__builtin_clz((unsigned)(hi-lo+1));
        return min(sp[j][lo], sp[j][hi-(1<<j)+1]);
    };

    // For each resident, find best chord (l,r) with r-l<=D maximizing
    //   benefit = (span - e) * eligibleTrafficProxy - setup,  span=r-l, e=bad(C,l,r)
    // We want e small (matching coupon) and span large and traffic high.
    // Strategy per resident: try a handful of candidate placements:
    //   - centered at high-traffic region with max span D
    //   - we scan windows of width up to D but that is O(L) per resident -> O(N*L)=25M ok.
    // For efficiency, for each resident we scan over r positions with l=r-D (max span),
    // and also consider trimming to reduce e. To bound time we just evaluate, for each
    // start l (step), the full-span chord. N*L could be 5000*5000=25M -> acceptable.

    // We hire greedily: compute candidate for each resident independently using flow proxy,
    // then sort by benefit and accept while subtracting captured traffic (re-derive flow
    // after each acceptance is too slow; instead we damp by marking captured segments).

    struct Cand{ long long ben; int i,l,r; };
    vector<Cand> cands;
    cands.reserve(N);

    // To keep O(N * something small): for each resident evaluate windows where l ranges
    // but step to cap work. We'll evaluate every possible l for residents but cap total.
    long long budget = 300000000LL; // ~300M window evaluations across all residents
    long long perRes = N>0 ? max(1LL, budget / N) : 1;

    for(int i=0;i<N;i++){
        int Di=D[i];
        char ci=C[i];
        long long bestBen=0; int bl=-1,br=-1;
        // Slide l from 0..L-1, with r = min(l+Di, L) (max span). Then for the best
        // l also try trimming r down to reduce edge cost e when that helps.
        long long span_count = L; // number of l positions
        int step = (int)max(1LL, span_count / perRes);
        for(int l=0;l<L; l+=step){
            int rmax=min(l+Di, L);
            if(rmax<=l) continue;
            // evaluate full span first
            int e=badR(ci,l,rmax);
            int span=rmax-l;
            if(span>e){
                long long tr = rminFlow(l+1, rmax);
                if(tr>0){
                    long long setup=(long long)H[i]+min(badR(ci,X[i],l),badR(ci,X[i],rmax));
                    long long ben=(long long)(span-e)*tr - setup;
                    if(ben>bestBen){ bestBen=ben; bl=l; br=rmax; }
                }
            }
        }
        if(bl>=0){
            cands.push_back({bestBen, i, bl, br});
        }
    }

    // Greedily accept candidates by benefit. Damp captured traffic by reducing flow
    // along chosen chord segments (so overlapping chords stop being attractive). Since
    // we already computed candidates with a fixed flow, instead we just accept all with
    // positive benefit but cap to avoid over-counting by limiting overlap: accept a chord
    // only if its captured segments still carry traffic > 0 in a mutable copy.
    sort(cands.begin(), cands.end(), [](const Cand&a,const Cand&b){return a.ben>b.ben;});

    vector<long long> mflow(flow.begin(), flow.end());
    vector<pair<int,int>> chosen(N, {-1,-1});
    for(auto&c:cands){
        // recheck eligible traffic with mutable flow
        long long tr = LLONG_MAX;
        for(int k=c.l+1;k<=c.r;k++){ tr=min(tr, mflow[k]); if(tr<=0) break; }
        if(tr<=0) continue;
        int e=badR(C[c.i], c.l, c.r);
        int span=c.r-c.l;
        long long setup=(long long)H[c.i]+min(badR(C[c.i],X[c.i],c.l),badR(C[c.i],X[c.i],c.r));
        long long ben=(long long)(span-e)*tr - setup;
        if(ben<=0) continue;
        // accept
        chosen[c.i]={c.l,c.r};
        // damp: subtract captured traffic from segments under the chord
        for(int k=c.l+1;k<=c.r;k++){ mflow[k]-=tr; if(mflow[k]<0) mflow[k]=0; }
    }

    // Output
    string out;
    out.reserve(N*6);
    char buf[32];
    for(int i=0;i<N;i++){
        if(chosen[i].first<0){ out+="-1\n"; }
        else{
            int n=snprintf(buf,sizeof(buf),"%d %d\n",chosen[i].first,chosen[i].second);
            out.append(buf,n);
        }
    }
    fputs(out.c_str(), stdout);
    return 0;
}
