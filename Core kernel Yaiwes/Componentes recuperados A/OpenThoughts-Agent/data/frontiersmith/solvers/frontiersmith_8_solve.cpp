#include <bits/stdc++.h>
using namespace std;

/*
 Resonant Bay Layout — heuristic.

 Place n oscillators on distinct integer bays in [0, m).
 Channel (u,v,w): energy = w * |sin(pi p_u/q_u d)| * |sin(pi p_v/q_v d)|, d=|x_u-x_v|.
 Maximize total energy F. Baseline = weighted-degree order spread evenly over [0,m-1].

 Approach: coordinate-descent / hill climbing over a bounded candidate-position pool.
 For each oscillator, given all others fixed, choose the distinct free position from the
 candidate pool that maximizes its incident-channel energy. Iterate to convergence.
 Seed from the baseline layout (so we never score below ~baseline), keep best seen.

 sin factor evaluated exactly as the judge does (periodic reduction with __int128).
*/

static inline double sinFactor(long long p, long long q, long long d){
    if(d==0) return 0.0;
    __int128 twoq = (__int128)2*q;
    __int128 pd = ((__int128)p % twoq) * ((__int128)(d % (2*q))) % twoq;
    // safer: full reduce
    pd = ((__int128)p * (__int128)d) % twoq;
    if(pd<0) pd += twoq;
    double angle = M_PI * (double)(long long)pd / (double)q;
    return fabs(sin(angle));
}

int main(){
    auto T_START = chrono::steady_clock::now();
    const double GLOBAL_DEADLINE = 7.0; // seconds, leave margin under 8s
    int t;
    if(scanf("%d",&t)!=1) return 0;
    string out;
    out.reserve(1<<20);
    char buf[24];

    std::mt19937_64 rng(12345);

    for(int tc=0;tc<t;tc++){
        int n; long long m; int r;
        scanf("%d %lld %d",&n,&m,&r);
        vector<long long> p(n+1), q(n+1);
        for(int i=1;i<=n;i++) scanf("%lld %lld",&p[i],&q[i]);
        vector<int> eu(r), ev(r); vector<long long> ew(r);
        vector<double> wdeg(n+1,0.0);
        vector<vector<int>> inc(n+1); // incident channel indices
        for(int i=0;i<r;i++){
            scanf("%d %d %lld",&eu[i],&ev[i],&ew[i]);
            wdeg[eu[i]]+=(double)ew[i];
            wdeg[ev[i]]+=(double)ew[i];
            inc[eu[i]].push_back(i);
            inc[ev[i]].push_back(i);
        }

        // baseline layout
        vector<int> order(n);
        for(int i=0;i<n;i++) order[i]=i+1;
        sort(order.begin(),order.end(),[&](int a,int b){
            if(wdeg[a]!=wdeg[b]) return wdeg[a]>wdeg[b];
            return a<b;
        });
        vector<long long> base(n+1,0);
        if(n==1) base[order[0]]=0;
        else for(int k=0;k<n;k++) base[order[k]]=(long long)k*(m-1)/(long long)(n-1);

        // Candidate position pool. We want distinct positions in [0,m).
        // Build a pool from: baseline positions, a dense small range [0, P), and some
        // structured offsets. Keep pool size modest so coordinate descent is fast.
        // For each oscillator move, we try all pool positions not currently used.
        // Target pool size: keep work per descent pass (~2*r*P) bounded.
        // Aim for 2*r*P <= ~60M so a pass is fast; clamp to a sane window.
        long long poolCap = r>0 ? (60000000LL/(2LL*r)) : 5000;
        if(poolCap < 2*n+64) poolCap = 2*n+64;
        if(poolCap > 6000) poolCap = 6000;
        set<long long> poolSet;
        for(int i=1;i<=n;i++) poolSet.insert(base[i]);
        // dense small range
        long long Pdense = min(m, max(64LL, min((long long)4*n, poolCap)));
        for(long long v=0; v<Pdense; v++) poolSet.insert(v);
        // large spreads for low-frequency oscillators (need big d)
        if(m>Pdense){
            long long step = max(1LL, (m-1)/ max(1LL, poolCap/2));
            for(long long v=0; v<m && (long long)poolSet.size()< (size_t)poolCap; v+=step) poolSet.insert(v);
            // some random positions
            for(int s=0;s<n+50 && (long long)poolSet.size()<poolCap; s++){
                long long v = (long long)(rng()% (unsigned long long)m);
                poolSet.insert(v);
            }
        }
        vector<long long> pool(poolSet.begin(), poolSet.end());
        int P = pool.size();

        // current assignment x[i] = position; used positions tracked by a map pos->osc
        vector<long long> x(n+1);
        for(int i=1;i<=n;i++) x[i]=base[i];

        // helper: energy contribution of oscillator i given current positions (over its channels)
        auto incEnergy=[&](int i, long long xi)->double{
            double s=0.0;
            for(int idx: inc[i]){
                int u=eu[idx], v=ev[idx];
                int o = (u==i)? v : u;
                long long d = llabs(xi - x[o]);
                if(d==0) continue;
                s += (double)ew[idx]*sinFactor(p[i],q[i],d)*sinFactor(p[o],q[o],d);
            }
            return s;
        };

        // total energy
        auto totalEnergy=[&]()->double{
            double s=0.0;
            for(int i=0;i<r;i++){
                long long d=llabs(x[eu[i]]-x[ev[i]]);
                if(d==0) continue;
                s+=(double)ew[i]*sinFactor(p[eu[i]],q[eu[i]],d)*sinFactor(p[ev[i]],q[ev[i]],d);
            }
            return s;
        };

        // occupancy
        unordered_map<long long,int> occ;
        occ.reserve(n*2);
        for(int i=1;i<=n;i++) occ[x[i]]=i;

        // best snapshot
        vector<long long> bestX = x;
        double bestF = totalEnergy();

        // Per-case deadline: split remaining global time over remaining cases.
        auto elapsedGlobal=[&]()->double{
            return chrono::duration<double>(chrono::steady_clock::now()-T_START).count();
        };
        double remain = GLOBAL_DEADLINE - elapsedGlobal();
        int casesLeft = t - tc;
        double caseBudget = remain / max(1,casesLeft);
        double caseDeadline = elapsedGlobal() + caseBudget;
        auto timeUp=[&]()->bool{ return elapsedGlobal()>=caseDeadline; };

        // process oscillators in order of decreasing degree (most constrained first)
        vector<int> procOrder = order;

        // one full coordinate-descent sweep; returns true if it converged (no improvement)
        auto descent=[&]()->void{
            bool improvedAny=true; int passes=0; int cnt=0;
            while(improvedAny){
                improvedAny=false;
                for(int i: procOrder){
                    double bestE = incEnergy(i, x[i]);
                    long long bestPos = x[i];
                    for(int pi=0; pi<P; pi++){
                        long long cand = pool[pi];
                        if(cand==x[i]) continue;
                        auto it=occ.find(cand);
                        if(it!=occ.end() && it->second!=i) continue;
                        double e = incEnergy(i, cand);
                        if(e>bestE+1e-9){ bestE=e; bestPos=cand; }
                    }
                    if(bestPos!=x[i]){
                        occ.erase(x[i]); x[i]=bestPos; occ[bestPos]=i;
                        improvedAny=true;
                    }
                    if(((++cnt)&63)==0 && timeUp()) return;
                }
                passes++;
                if(timeUp()) return;
                if(passes>100) return;
            }
        };

        // Swap-based local improvement: try swapping positions of pairs of oscillators.
        // Essential when bays are saturated (m close to n) so single moves are blocked.
        auto swapDescent=[&]()->void{
            bool imp=true; int guard=0;
            while(imp){
                imp=false;
                for(int a=1;a<=n;a++){
                    for(int b=a+1;b<=n;b++){
                        // current incident energy of a and b
                        double before = incEnergy(a,x[a]) + incEnergy(b,x[b]);
                        // if a and b share a channel it's counted twice in both before/after
                        // consistently, so the delta comparison is still valid.
                        long long xa=x[a], xb=x[b];
                        // tentatively swap
                        x[a]=xb; x[b]=xa;
                        double after = incEnergy(a,x[a]) + incEnergy(b,x[b]);
                        if(after > before + 1e-9){
                            occ[xb]=a; occ[xa]=b; imp=true;
                        } else {
                            x[a]=xa; x[b]=xb; // revert
                        }
                    }
                    if(((++guard)&31)==0 && timeUp()) return;
                }
                if(timeUp()) return;
            }
        };

        descent();
        swapDescent();
        {double F=totalEnergy(); if(F>bestF){ bestF=F; bestX=x; }}

        // Random restarts with perturbation while time remains for this case.
        while(!timeUp()){
            x = bestX;
            occ.clear();
            for(int i=1;i<=n;i++) occ[x[i]]=i;
            int kick = max(1, n/5);
            for(int s=0;s<kick;s++){
                int i = 1 + (int)(rng()%n);
                long long cand = pool[rng()%P];
                if(occ.count(cand) && occ[cand]!=i) continue;
                occ.erase(x[i]); x[i]=cand; occ[cand]=i;
            }
            descent();
            swapDescent();
            double f2=totalEnergy();
            if(f2>bestF){ bestF=f2; bestX=x; }
        }

        // emit bestX (guaranteed feasible: distinct positions within [0,m))
        for(int i=1;i<=n;i++){
            int nb=snprintf(buf,sizeof(buf),"%lld",bestX[i]);
            out.append(buf,nb);
            out.push_back(i<n?' ':'\n');
        }
    }
    fputs(out.c_str(), stdout);
    return 0;
}
