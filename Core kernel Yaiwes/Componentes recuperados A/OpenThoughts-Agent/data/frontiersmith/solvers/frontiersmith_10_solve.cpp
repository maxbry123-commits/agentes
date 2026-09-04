// Frontiersmith 10: Quadratic Witness Packing (heuristic)
// Strategy: a witness (A,B) realizes value S=A^2+B^2; it covers query i iff S mod p_i == x_i.
// For each modulus p, the heaviest residue x usually dominates. We greedily pack
// pairwise-coprime moduli (with their best residue) into a single witness via CRT, keeping
// the CRT modulus M <= min(Bound, ~2e9) so the realized coords A,B (< M) stay within [0,Bound].
// We realize each combined residue R mod M as A^2+B^2 by trying small A, then solving
// B^2 == (R - A^2) mod p for each prime factor p of M with Tonelli-Shanks + CRT.
#include <bits/stdc++.h>
using namespace std;

typedef long long ll;
typedef unsigned long long ull;
typedef __int128 lll;

static inline ll mulmod(ll a, ll b, ll m){ return (ll)((lll)a*b % m); }
static inline ll powmod(ll a, ll e, ll m){ ll r=1%m; a%=m; if(a<0)a+=m; while(e){ if(e&1) r=mulmod(r,a,m); a=mulmod(a,a,m); e>>=1;} return r; }

// Tonelli-Shanks: sqrt of n mod prime p, or -1 if no solution
static ll tonelli(ll n, ll p){
    n%=p; if(n<0)n+=p;
    if(n==0) return 0;
    if(p==2) return n;
    if(powmod(n,(p-1)/2,p)!=1) return -1;
    if(p%4==3) return powmod(n,(p+1)/4,p);
    ll q=p-1, s=0; while((q&1)==0){q>>=1;s++;}
    ll z=2; while(powmod(z,(p-1)/2,p)!=p-1) z++;
    ll m=s, c=powmod(z,q,p), t=powmod(n,q,p), r=powmod(n,(q+1)/2,p);
    while(t!=1){
        ll i=0, tt=t; while(tt!=1){ tt=mulmod(tt,tt,p); i++; if(i==m) return -1; }
        ll b=powmod(c, 1LL<<(m-i-1), p);
        m=i; c=mulmod(b,b,p); t=mulmod(t,c,p); r=mulmod(r,b,p);
    }
    return r;
}

// extended gcd
static ll gcdll(ll a, ll b){ while(b){ ll t=a%b; a=b; b=t; } return a<0?-a:a; }
static ll egcd(ll a, ll b, ll &x, ll &y){ if(!b){x=1;y=0;return a;} ll x1,y1; ll g=egcd(b,a%b,x1,y1); x=y1; y=x1-(a/b)*y1; return g; }
static ll modinv(ll a, ll m){ ll x,y; egcd((a%m+m)%m,m,x,y); return ((x%m)+m)%m; }

// factorize n (odd squarefree, up to 1e7): trial division
static void factorize(ll n, vector<ll>&fs){
    for(ll d=3; d*d<=n; d+=2){ if(n%d==0){ fs.push_back(d); n/=d; } }
    if(n>1) fs.push_back(n);
}

// CRT combine: result ≡ rs[i] mod ms[i] (ms pairwise coprime). returns (R,M)
static pair<ll,ll> crt(const vector<ll>&rs, const vector<ll>&ms){
    ll R=0, M=1;
    for(size_t i=0;i<ms.size();i++){
        ll m=ms[i], r=((rs[i]%m)+m)%m;
        ll inv=modinv(M%m, m);
        ll t=mulmod(((r - R%m)%m + m)%m, inv, m);
        R = R + M*t; M = M*m; R%=M;
    }
    return {R%M, M};
}

int main(){
    // fast input
    static char buf[1<<25];
    int rd = fread(buf,1,sizeof(buf),stdin);
    int total = rd; string extra;
    // if input bigger than buffer, read rest
    while(rd==(int)sizeof(buf)){
        string more; more.resize(1<<25);
        rd = fread(&more[0],1,more.size(),stdin);
        extra.append(more.data(), rd);
        total += rd;
    }
    string data; data.reserve(total);
    data.append(buf, (size_t)min(total,(int)sizeof(buf)));
    if(total>(int)sizeof(buf)) data.append(extra);
    const char* s = data.data();
    const char* end = s + data.size();
    auto readInt = [&]()->ll{
        while(s<end && (*s<'0'||*s>'9') && *s!='-') s++;
        bool neg=false; if(s<end && *s=='-'){neg=true;s++;}
        ll v=0; while(s<end && *s>='0'&&*s<='9'){ v=v*10+(*s-'0'); s++; }
        return neg?-v:v;
    };

    ll n=readInt(), K=readInt(), Bound=readInt();
    vector<ll> P(n), X(n), Wt(n);
    for(ll i=0;i<n;i++){ P[i]=readInt(); X[i]=readInt(); Wt[i]=readInt(); }

    // group by (p,x) -> weight; also per modulus best residue
    // use hashmap keyed by p*BIG + x is risky (p up to 1e7, x<p<1e7) -> key = p* (1e7+1) + x fits in ll
    unordered_map<ull,ll> grp; grp.reserve(n*2);
    const ull MULT = 10000001ULL;
    for(ll i=0;i<n;i++){ grp[(ull)P[i]*MULT + (ull)X[i]] += Wt[i]; }

    // per modulus: best residue (max weight)
    // map p -> (bestWeight, bestX)
    unordered_map<ll, pair<ll,ll>> best; best.reserve(grp.size());
    for(auto&kv: grp){
        ll p = (ll)(kv.first / MULT);
        ll x = (ll)(kv.first % MULT);
        ll w = kv.second;
        auto it = best.find(p);
        if(it==best.end() || w>it->second.first) best[p] = {w, x};
    }
    // sort moduli by best-residue weight desc
    vector<tuple<ll,ll,ll>> items; items.reserve(best.size()); // (weight, p, x)
    for(auto&kv: best) items.push_back({kv.second.first, kv.first, kv.second.second});
    sort(items.begin(), items.end(), [](const auto&a, const auto&b){ return get<0>(a)>get<0>(b); });

    // distinct moduli list
    vector<ll> moduli; moduli.reserve(best.size());
    for(auto&kv: best) moduli.push_back(kv.first);

    vector<pair<ll,ll>> witnesses; // (A,B)

    // ---- SMALL-BOUND BRANCH ----
    // When Bound is small, the set of achievable witness values S=A^2+B^2 (0<=A,B<=Bound)
    // is small; enumerate distinct S, score each by total covered weight = sum over distinct
    // moduli p of grp[(p, S mod p)], then greedily pick K via weighted max-coverage.
    // (Bound+1)^2/2 candidates; cheap when Bound <= ~3000.
    if(Bound <= 3000){
        // enumerate distinct S and remember a realizing (A,B)
        unordered_map<ll,pair<ll,ll>> Smap; Smap.reserve((size_t)(Bound+1)*(Bound+2)/2);
        for(ll A=0;A<=Bound;A++){
            ll A2=A*A;
            for(ll B=A;B<=Bound;B++){
                ll S=A2+B*B;
                if(Smap.find(S)==Smap.end()) Smap[S]={A,B};
            }
        }
        // candidate list of S
        vector<ll> cand; cand.reserve(Smap.size());
        for(auto&kv:Smap) cand.push_back(kv.first);
        ll C=(ll)cand.size();
        // covered flag per (p,x)-group: greedy max-coverage. Track which groups already covered.
        // Represent groups by their key in grp. For marginal gain we recompute remaining.
        // Build, for each candidate, the list of group-keys it covers (with weights), once.
        // Memory: sum over candidates of #moduli — C*|moduli|. For Bound=100 (C~5000) * moduli(200)=1e6 ok.
        // For Bound up to 3000 -> C~4.5e6 * moduli ... could be large; guard by moduli count.
        // We'll just recompute marginal each round (K rounds) -> K * C * |moduli| lookups.
        vector<char> groupCovered; // not used; use a set of covered keys
        unordered_set<ull> covered; covered.reserve(grp.size());
        // precompute per-candidate covered keys to speed marginal recompute
        // To bound memory, only do precompute if C*moduli small
        bool precomp = ((double)C * (double)moduli.size() <= 8e6);
        vector<vector<ull>> candKeys; // keys covered (only if precomp)
        if(precomp){
            candKeys.resize(C);
            for(ll ci=0; ci<C; ci++){
                ll S=cand[ci];
                auto &v=candKeys[ci];
                for(ll p: moduli){
                    ll r=S%p;
                    ull key=(ull)p*MULT+(ull)r;
                    if(grp.find(key)!=grp.end()) v.push_back(key);
                }
            }
        }
        vector<char> candUsed(C,0);
        for(ll round=0; round<K; round++){
            ll bestGain=-1, bestCi=-1;
            for(ll ci=0; ci<C; ci++){
                if(candUsed[ci]) continue;
                ll gain=0;
                if(precomp){
                    for(ull key: candKeys[ci]) if(!covered.count(key)) gain+=grp[key];
                } else {
                    ll S=cand[ci];
                    for(ll p: moduli){
                        ull key=(ull)p*MULT+(ull)(S%p);
                        auto it=grp.find(key);
                        if(it!=grp.end() && !covered.count(key)) gain+=it->second;
                    }
                }
                if(gain>bestGain){ bestGain=gain; bestCi=ci; }
            }
            if(bestCi<0 || bestGain<=0) break;
            candUsed[bestCi]=1;
            // mark covered
            ll S=cand[bestCi];
            if(precomp){ for(ull key: candKeys[bestCi]) covered.insert(key); }
            else { for(ll p: moduli){ ull key=(ull)p*MULT+(ull)(S%p); if(grp.count(key)) covered.insert(key);} }
            witnesses.push_back(Smap[S]);
        }
        // pad to <=K with simple distinct witnesses (j,0)
        ll j=0;
        while(witnesses.size()<(size_t)K && j<=Bound){ witnesses.push_back({j,0}); j++; }
        // output and return
        string out; out.reserve(witnesses.size()*8+16);
        out += to_string((ll)witnesses.size()); out += '\n';
        for(auto&ab: witnesses){ out += to_string(ab.first); out += ' '; out += to_string(ab.second); out += '\n'; }
        fwrite(out.data(),1,out.size(),stdout);
        return 0;
    }

    ll Mcap = min(Bound, (ll)2000000000LL);

    // ---- LARGE-BOUND BRANCH (coverage-aware greedy) ----
    // Build a pool of candidate witness values S. Each candidate is grown by CRT from a "seed"
    // heavy (p,x) group, then extended with additional heavy compatible groups (coprime modulus,
    // product <= Mcap) to bundle more weight into one S. Then realize S as A^2+B^2 (coords<=Bound).
    // Finally greedily select K candidates maximizing marginal TOTAL coverage (over ALL moduli,
    // not just the seeded ones) — this captures incidental coverage and is robust when weight is
    // spread thin.
    //
    // realize combined residue given as prime-factor residues -> (A,B) with coords<=Bound, or fail.
    auto realizeFactors = [&](vector<ll>&pf, vector<ll>&fr, ll &outA, ll &outB)->bool{
        auto RM = crt(fr, pf); ll R=RM.first, Mfull=RM.second;
        ll Acap = min(Bound,(ll)400000);
        for(ll A=0; A<=Acap; A++){
            ll Asq = mulmod(A%Mfull, A%Mfull, Mfull);
            ll c = ((R-Asq)%Mfull+Mfull)%Mfull;
            bool good=true; static vector<ll> bs; bs.clear();
            for(ll f: pf){ ll b=tonelli(c%f,f); if(b<0){good=false;break;} bs.push_back(b); }
            if(good){ auto BM=crt(bs,pf); ll B=BM.first; if(B<=Bound&&A<=Bound){ outA=A; outB=B; return true; } }
        }
        return false;
    };

    // candidate S values + their realizations
    vector<ll> candS; vector<pair<ll,ll>> candAB;
    int seedLimit = (int)min((ll)items.size(), (ll)2000); // seeds from heaviest groups
    for(int si=0; si<seedLimit; si++){
        ll p0=get<1>(items[si]), x0=get<2>(items[si]);
        vector<ll> pf, fr; ll M=1;
        { vector<ll> fs; factorize(p0,fs); for(ll f:fs){ pf.push_back(f); fr.push_back(((x0%f)+f)%f);} M=p0; }
        // greedily extend with other heavy groups (scan a limited window) that stay coprime & under cap
        int ext=0;
        for(int sj=0; sj<seedLimit && ext<40; sj++){
            if(sj==si) continue;
            ll p=get<1>(items[sj]), x=get<2>(items[sj]);
            if((double)M*(double)p > (double)Mcap) continue;
            if(gcdll(M,p)!=1) continue;
            vector<ll> fs; factorize(p,fs); for(ll f:fs){ pf.push_back(f); fr.push_back(((x%f)+f)%f);} M*=p; ext++;
        }
        ll A,B;
        if(realizeFactors(pf,fr,A,B)){
            candS.push_back(A*A+B*B); candAB.push_back({A,B});
        } else {
            // fallback: realize just the seed group
            vector<ll> pf2,fr2; vector<ll> fs; factorize(p0,fs); for(ll f:fs){pf2.push_back(f);fr2.push_back(((x0%f)+f)%f);}
            if(realizeFactors(pf2,fr2,A,B)){ candS.push_back(A*A+B*B); candAB.push_back({A,B}); }
        }
    }
    // dedup candidates by S
    {
        unordered_map<ll,int> seen; vector<ll> ns; vector<pair<ll,ll>> nab;
        for(size_t i=0;i<candS.size();i++){ if(seen.find(candS[i])==seen.end()){ seen[candS[i]]=1; ns.push_back(candS[i]); nab.push_back(candAB[i]); } }
        candS.swap(ns); candAB.swap(nab);
    }

    // Greedy weighted max-coverage selecting K candidates by marginal total coverage.
    // Precompute, once, each candidate's covered (key,weight) list. Then each round recomputes
    // marginal gain by skipping already-covered keys (only over a candidate's own key list).
    int C=(int)candS.size();
    vector<vector<pair<ull,ll>>> candKW(C); // (key, weight) for each candidate
    for(int ci=0; ci<C; ci++){
        ll S=candS[ci];
        auto &v=candKW[ci];
        for(ll p: moduli){
            ull key=(ull)p*MULT + (ull)(S%p);
            auto it=grp.find(key);
            if(it!=grp.end()) v.push_back({key, it->second});
        }
    }
    unordered_set<ull> covered; covered.reserve(grp.size());
    vector<char> used(C,0);
    for(int round=0; round<K && (int)witnesses.size()<K; round++){
        ll bestGain=-1; int bestCi=-1;
        for(int ci=0; ci<C; ci++){
            if(used[ci]) continue;
            ll gain=0;
            for(auto&kw: candKW[ci]) if(!covered.count(kw.first)) gain+=kw.second;
            if(gain>bestGain){ bestGain=gain; bestCi=ci; }
        }
        if(bestCi<0 || bestGain<=0) break;
        used[bestCi]=1;
        for(auto&kw: candKW[bestCi]) covered.insert(kw.first);
        witnesses.push_back(candAB[bestCi]);
    }

    // Pad remaining slots with distinct (j,0) — harmless extra QR coverage.
    {
        ll j=0;
        while(witnesses.size()<(size_t)K && j<=Bound){ witnesses.push_back({j,0}); j++; }
    }

    // Output
    string out;
    out.reserve(witnesses.size()*22 + 16);
    out += to_string((ll)witnesses.size()); out += '\n';
    for(auto&ab: witnesses){
        out += to_string(ab.first); out += ' '; out += to_string(ab.second); out += '\n';
    }
    fwrite(out.data(),1,out.size(),stdout);
    return 0;
}
