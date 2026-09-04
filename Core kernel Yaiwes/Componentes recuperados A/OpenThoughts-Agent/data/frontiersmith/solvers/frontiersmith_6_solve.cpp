#include <bits/stdc++.h>
using namespace std;
typedef long double ld;

static int N, K;
static ld P, A, B;
static vector<ld> sx, sy, sd;

static std::mt19937 rng(12345);

// Welzl-ish min enclosing circle (returns center; r2 computed by caller as max dist).
// For robustness with large N we use a simple but exact-ish approach via Welzl on the
// subset of points assigned to a cluster. N small in tests so this is fine; for huge N
// we fall back to centroid + a couple of refinement passes.

struct Pt { ld x, y; };

static inline ld dist2(ld ax, ld ay, ld bx, ld by){ ld dx=ax-bx, dy=ay-by; return dx*dx+dy*dy; }

// circle from 2 / 3 points
static void circ2(const Pt&a,const Pt&b, ld&cx,ld&cy){ cx=(a.x+b.x)/2; cy=(a.y+b.y)/2; }
static bool circ3(const Pt&a,const Pt&b,const Pt&c, ld&cx,ld&cy){
    ld ax=a.x,ay=a.y,bx=b.x,by=b.y,cx3=c.x,cy3=c.y;
    ld d=2*(ax*(by-cy3)+bx*(cy3-ay)+cx3*(ay-by));
    if (fabsl(d) < 1e-18L) return false;
    ld ux=((ax*ax+ay*ay)*(by-cy3)+(bx*bx+by*by)*(cy3-ay)+(cx3*cx3+cy3*cy3)*(ay-by))/d;
    ld uy=((ax*ax+ay*ay)*(cx3-bx)+(bx*bx+by*by)*(ax-cx3)+(cx3*cx3+cy3*cy3)*(bx-ax))/d;
    cx=ux; cy=uy; return true;
}

// Welzl on vector of points -> center (cx,cy). Works for any size but O(n) expected.
static void mec(vector<Pt>& pts, ld& cx, ld& cy){
    int n=pts.size();
    if(n==0){cx=0;cy=0;return;}
    if(n==1){cx=pts[0].x;cy=pts[0].y;return;}
    shuffle(pts.begin(),pts.end(),rng);
    cx=pts[0].x; cy=pts[0].y; ld r2=0;
    for(int i=1;i<n;i++){
        if(dist2(cx,cy,pts[i].x,pts[i].y) <= r2 + 1e-12L) continue;
        cx=pts[i].x; cy=pts[i].y; r2=0;
        for(int j=0;j<i;j++){
            if(dist2(cx,cy,pts[j].x,pts[j].y) <= r2 + 1e-12L) continue;
            circ2(pts[i],pts[j],cx,cy);
            r2=dist2(cx,cy,pts[i].x,pts[i].y);
            for(int kk=0;kk<j;kk++){
                if(dist2(cx,cy,pts[kk].x,pts[kk].y) <= r2 + 1e-12L) continue;
                ld ncx,ncy;
                if(circ3(pts[i],pts[j],pts[kk],ncx,ncy)){
                    cx=ncx; cy=ncy; r2=dist2(cx,cy,pts[i].x,pts[i].y);
                }
            }
        }
    }
}

// For large clusters, approximate center: bounding-box center then refine by moving toward
// farthest point a few iterations (1-center / smallest enclosing circle approximation).
static void approxCenter(const vector<int>& idx, ld& cx, ld& cy){
    int n=idx.size();
    ld minx=1e30L,maxx=-1e30L,miny=1e30L,maxy=-1e30L;
    for(int j:idx){ minx=min(minx,sx[j]);maxx=max(maxx,sx[j]);miny=min(miny,sy[j]);maxy=max(maxy,sy[j]); }
    cx=(minx+maxx)/2; cy=(miny+maxy)/2;
    // refinement: move toward farthest point with decreasing step
    ld step=0.5L;
    for(int it=0; it<60; it++){
        int far=idx[0]; ld fd=-1;
        for(int j:idx){ ld d=dist2(cx,cy,sx[j],sy[j]); if(d>fd){fd=d;far=j;} }
        cx += (sx[far]-cx)*step;
        cy += (sy[far]-cy)*step;
        step *= 0.95L;
    }
}

// Given assignment (asg[j] in [0,M)), compute center for each cluster and total cost.
static ld evalCost(int M, const vector<int>& asg, vector<ld>& cx, vector<ld>& cy){
    vector<vector<int>> members(M);
    for(int j=0;j<N;j++) members[asg[j]].push_back(j);
    cx.assign(M,0); cy.assign(M,0);
    ld total=0;
    for(int i=0;i<M;i++){
        if(members[i].empty()) continue;
        if((int)members[i].size() <= 2000){
            vector<Pt> pts; pts.reserve(members[i].size());
            for(int j:members[i]) pts.push_back({sx[j],sy[j]});
            mec(pts,cx[i],cy[i]);
        } else {
            approxCenter(members[i],cx[i],cy[i]);
        }
        ld r2=0, L=0;
        for(int j:members[i]){ ld d=dist2(cx[i],cy[i],sx[j],sy[j]); if(d>r2)r2=d; L+=sd[j]; }
        total += P + A*r2 + B*L*L;
    }
    return total;
}

int main(){
    // fast input
    {
        ios::sync_with_stdio(false);
        cin.tie(nullptr);
    }
    if(!(cin>>N>>K)) return 0;
    cin>>P>>A>>B;
    sx.resize(N); sy.resize(N); sd.resize(N);
    for(int j=0;j<N;j++) cin>>sx[j]>>sy[j]>>sd[j];

    // ---------- Build baseline solution (replicate judge baseline exactly) ----------
    vector<int> order(N);
    iota(order.begin(),order.end(),0);
    sort(order.begin(),order.end(),[&](int a,int b){
        if(sx[a]!=sx[b]) return sx[a]<sx[b];
        if(sy[a]!=sy[b]) return sy[a]<sy[b];
        return a<b;
    });
    // baseline uses K blocks; produce assignment with M=K (empty blocks allowed but we need M>=1)
    auto buildBaseline = [&](int Kuse, vector<int>& asg)->int{
        asg.assign(N,0);
        int realM=0;
        vector<int> blockOfHub; // not needed; we map nonempty blocks to hub ids
        // assign hub id = block index (0-based); but need contiguous 1..M. We'll keep block id then compress.
        vector<int> blockId(N);
        for(int t=1;t<=Kuse;t++){
            long long lo=(long long)(t-1)*N/Kuse;
            long long hi=(long long)t*N/Kuse;
            for(long long i=lo;i<hi;i++) blockId[order[i]]=t-1;
        }
        // compress nonempty blocks
        vector<int> remap(Kuse,-1);
        for(int j=0;j<N;j++) if(remap[blockId[j]]<0) remap[blockId[j]]=0;
        int next=0;
        for(int b=0;b<Kuse;b++) if(remap[b]==0) remap[b]=next++;
        // careful: above sets all seen to 0 first. redo properly:
        fill(remap.begin(),remap.end(),-1);
        next=0;
        for(int b=0;b<Kuse;b++){
            bool any=false;
            // determine if block b is nonempty
        }
        // simpler: count membership
        vector<int> cnt(Kuse,0);
        for(int j=0;j<N;j++) cnt[blockId[j]]++;
        next=0;
        for(int b=0;b<Kuse;b++) if(cnt[b]>0) remap[b]=next++;
        for(int j=0;j<N;j++) asg[j]=remap[blockId[j]];
        realM=next;
        return realM;
    };

    vector<int> bestAsg; int bestM;
    bestM = buildBaseline(K, bestAsg);
    vector<ld> bcx,bcy;
    ld bestCost = evalCost(bestM, bestAsg, bcx, bcy);

    // ---------- K-means style improvement over multiple M and restarts ----------
    // Time budget control
    auto t0 = chrono::steady_clock::now();
    auto timeLeft = [&](double lim)->bool{
        return chrono::duration<double>(chrono::steady_clock::now()-t0).count() < lim;
    };
    double TLIM = (N>20000)?2.3:3.2; // safety under 4s

    // Lloyd's algorithm with given M and an initial centers set.
    auto lloyd = [&](int M, vector<ld>& cxs, vector<ld>& cys, vector<int>& asg)->ld{
        asg.assign(N,0);
        ld prev=1e300L;
        int maxIter = (N>20000)?12:50;
        for(int iter=0; iter<maxIter; iter++){
            if(!timeLeft(TLIM)) break;
            // assign each sensor to nearest center (by distance; this is a heuristic proxy)
            for(int j=0;j<N;j++){
                ld bd=1e30L; int bi=0;
                for(int i=0;i<M;i++){ ld d=dist2(cxs[i],cys[i],sx[j],sy[j]); if(d<bd){bd=d;bi=i;} }
                asg[j]=bi;
            }
            // recompute centers as MEC
            vector<ld> ncx,ncy;
            ld cost=evalCost(M,asg,ncx,ncy);
            // for empty clusters keep old center
            for(int i=0;i<M;i++){
                bool empty=true;
                // detect empties via cost recompute: ncx left 0; just check membership
            }
            // recompute membership to keep centers for empties
            vector<int> cnt(M,0);
            for(int j=0;j<N;j++) cnt[asg[j]]++;
            for(int i=0;i<M;i++){ if(cnt[i]==0){ ncx[i]=cxs[i]; ncy[i]=cys[i]; } }
            cxs=ncx; cys=ncy;
            if(fabsl(prev-cost) < 1e-9L) { prev=cost; break; }
            prev=cost;
        }
        return prev;
    };

    int restartsPerM = (N<=200)?40:(N<=2000?8:2);

    for(int M=1; M<=K && timeLeft(TLIM); M++){
        for(int rs=0; rs<restartsPerM && timeLeft(TLIM); rs++){
            vector<ld> cxs(M), cys(M);
            if(rs==0){
                // seed from sorted-block centroids (like baseline) for this M
                vector<int> tmp; int rm=buildBaseline(M,tmp);
                // get centers
                vector<ld> tcx,tcy; evalCost(rm,tmp,tcx,tcy);
                // if rm<M pad with random points
                for(int i=0;i<M;i++){
                    if(i<rm){cxs[i]=tcx[i];cys[i]=tcy[i];}
                    else { int j=rng()%N; cxs[i]=sx[j]; cys[i]=sy[j]; }
                }
            } else {
                // random seeds (kmeans++ lite)
                int first=rng()%N; cxs[0]=sx[first]; cys[0]=sy[first];
                for(int i=1;i<M;i++){
                    // pick point far from chosen
                    ld bd=-1; int bj=0;
                    for(int tries=0;tries<min(N,64);tries++){
                        int j=rng()%N; ld md=1e30L;
                        for(int q=0;q<i;q++){ ld d=dist2(cxs[q],cys[q],sx[j],sy[j]); if(d<md)md=d; }
                        if(md>bd){bd=md;bj=j;}
                    }
                    cxs[i]=sx[bj]; cys[i]=sy[bj];
                }
            }
            vector<int> asg;
            ld cost=lloyd(M,cxs,cys,asg);
            if(cost < bestCost - 1e-9L){
                bestCost=cost; bestAsg=asg; bestM=M;
                evalCost(bestM,bestAsg,bcx,bcy);
            }
        }
    }

    // ---------- Local move improvement: try moving single sensors to other hubs ----------
    if(N<=5000){
        bool improved=true; int passes=0;
        while(improved && passes<20 && timeLeft(TLIM)){
            improved=false; passes++;
            // recompute current centers/cost
            evalCost(bestM,bestAsg,bcx,bcy);
            for(int j=0;j<N && timeLeft(TLIM); j++){
                int cur=bestAsg[j];
                for(int tgt=0; tgt<bestM; tgt++){
                    if(tgt==cur) continue;
                    vector<int> trial=bestAsg; trial[j]=tgt;
                    vector<ld> tcx,tcy;
                    ld c=evalCost(bestM,trial,tcx,tcy);
                    if(c < bestCost - 1e-9L){
                        bestCost=c; bestAsg=trial; improved=true; break;
                    }
                }
            }
        }
    }

    // ---------- Final safety: ensure assignment valid & M>=1 ----------
    // Recompute final centers
    evalCost(bestM,bestAsg,bcx,bcy);
    // Remap to contiguous 1..M' and only output used hubs (but judge ignores empties; keep simple).
    // Ensure every asg in [0,bestM). Compress to used hubs:
    vector<int> used(bestM,-1); int nm=0;
    for(int j=0;j<N;j++){ if(used[bestAsg[j]]<0) used[bestAsg[j]]=nm++; }
    if(nm==0){ // shouldn't happen
        nm=1; used.assign(bestM,0);
    }
    // collect centers of used hubs
    vector<ld> ocx(nm), ocy(nm);
    for(int i=0;i<bestM;i++) if(used[i]>=0){ ocx[used[i]]=bcx[i]; ocy[used[i]]=bcy[i]; }

    // clamp coords to 1e9 just in case
    for(int i=0;i<nm;i++){
        if(!(ocx[i]==ocx[i])) ocx[i]=0; if(!(ocy[i]==ocy[i])) ocy[i]=0;
        ocx[i]=max((ld)-1e9L,min((ld)1e9L,ocx[i]));
        ocy[i]=max((ld)-1e9L,min((ld)1e9L,ocy[i]));
    }

    // ---------- Output ----------
    {
        std::ostringstream out;
        out.setf(std::ios::fixed); out<<setprecision(9);
        out<<nm<<"\n";
        for(int i=0;i<nm;i++) out<<(double)ocx[i]<<" "<<(double)ocy[i]<<"\n";
        for(int j=0;j<N;j++){ out<<(used[bestAsg[j]]+1); out<<(j+1<N?' ':'\n'); }
        cout<<out.str();
    }
    return 0;
}
