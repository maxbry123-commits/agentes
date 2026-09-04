#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

int n, m, t, k;
vector<ll> a;      // residue mod m (0-indexed nodes 0..n-1, node i = input i+1)
vector<ll> c;
vector<int> par;
vector<vector<int>> children;
vector<int> bfsOrder;
vector<int> tin, tout, eulerNode;
vector<int> primes;
int Psize;
vector<int> primeIdx; // residue -> prime index, -1 if not prime
vector<int> sObs;     // observatory subtree-root (0-indexed node)
vector<ll> wObs;

// cumulative shift per node (current solution)
vector<ll> cumshift;

// time
chrono::steady_clock::time_point T0;
double elapsed(){ return chrono::duration<double>(chrono::steady_clock::now()-T0).count(); }
const double TLIM = 3.7; // hard limit 5s

static inline int residueOf(int node){ return (int)((a[node]+cumshift[node]) % m); }

// ---- Objective evaluation ----
// We maintain, in euler order, the residue of each node. For each observatory range
// [lo,hi], C_j = # distinct primes present. We compute total penalty.
//
// For efficiency we use: for each prime index pi, a sorted vector of euler positions
// where current residue == primes[pi]. Then a range [lo,hi] covers prime pi iff
// lower_bound on that list finds a position <= hi within [lo,hi].
// Rebuilding all lists is O(n). Counting C_j per observatory is O(Psize*log n) which is
// too slow for big cases — so we use a different counting method:
//
// counting distinct values in many ranges: process observatories offline.
// We use the standard "last occurrence" BIT trick: sort observatories by hi.
// For position pos from 0..n-1 in euler order with prime-index pv (or none):
//   maintain BIT where for each prime we keep only its LAST seen position marked.
//   When we see prime pv at pos: if it had a previous marked position, unset it; set pos.
//   For observatory with this hi: C_j = number of marked positions in [lo,hi]
//     = prefix(hi)-prefix(lo-1) over the BIT (count of marks). Distinctness guaranteed
//     because each prime marks only its latest position; a prime present in [lo,hi]
//     has its last-occurrence <= hi, and that last occ is >= lo iff it appears in range
//     ... NOT exactly: last occ could be < lo while an earlier occ is in range? No:
//     last occ is the LARGEST position <= current hi. If last occ < lo, then all occ < lo
//     (since last is largest), so prime not in [lo,hi]. If last occ in [lo,hi], counted.
//   This is the classic "count distinct in range" offline algorithm. Correct.
//
// Complexity: O((n + t) log n) per full evaluation. Good even for 1e5.

struct BIT {
    int N; vector<int> b;
    void init(int n_){ N=n_; b.assign(N+1,0); }
    void add(int i,int v){ for(++i;i<=N;i+=i&-i) b[i]+=v; }
    int sum(int i){ int s=0; for(++i;i>0;i-=i&-i) s+=b[i]; return s; } // prefix [0..i]
    int range(int l,int r){ if(r<l) return 0; return sum(r)-(l>0?sum(l-1):0); }
};

// Precomputed observatory order by hi
vector<int> obsOrderByHi;

ll computeObjective(ll retunerCost){
    // residue per euler position
    static vector<int> resPos; resPos.assign(n, -1);
    for(int pos=0; pos<n; pos++){
        int node=eulerNode[pos];
        int r=(int)((a[node]+cumshift[node])%m);
        resPos[pos]= (primeIdx[r]>=0)? primeIdx[r] : -1;
    }
    BIT bit; bit.init(n);
    vector<int> lastPos(Psize, -1);
    ll totalPenalty=0;
    int oi=0;
    // observatories sorted by hi (tout[s_j])
    // process positions, answer observatories whose hi == pos after marking pos
    // We need to answer when current processed prefix covers up to hi. Process pos 0..n-1,
    // after marking pos, answer all observatories with hi==pos.
    // Build buckets: obs indexed by hi.
    static vector<vector<int>> byHi;
    static bool builtBuckets=false;
    if(!builtBuckets){
        byHi.assign(n, {});
        for(int j=0;j<t;j++) byHi[tout[sObs[j]]].push_back(j);
        builtBuckets=true;
    }
    for(int pos=0; pos<n; pos++){
        int pv=resPos[pos];
        if(pv>=0){
            if(lastPos[pv]>=0) bit.add(lastPos[pv], -1);
            bit.add(pos, +1);
            lastPos[pv]=pos;
        }
        for(int j: byHi[pos]){
            int lo=tin[sObs[j]], hi=pos;
            int cov=bit.range(lo,hi);
            totalPenalty += wObs[j]*(ll)(Psize - cov);
        }
    }
    return totalPenalty + retunerCost;
}

int main(){
    T0=chrono::steady_clock::now();
    ios::sync_with_stdio(false); cin.tie(nullptr);
    if(!(cin>>n>>m>>t>>k)) return 0;
    a.resize(n); c.resize(n);
    for(int i=0;i<n;i++){ ll x; cin>>x; a[i]=((x%m)+m)%m; }
    for(int i=0;i<n;i++) cin>>c[i];
    vector<vector<int>> adj(n);
    for(int i=0;i<n-1;i++){ int u,v; cin>>u>>v; --u;--v; adj[u].push_back(v); adj[v].push_back(u); }
    sObs.resize(t); wObs.resize(t);
    for(int j=0;j<t;j++){ int s; ll w; cin>>s>>w; sObs[j]=s-1; wObs[j]=w; }

    // root at node 0 (input node 1), BFS
    par.assign(n,-1); bfsOrder.reserve(n);
    {
        vector<char> vis(n,0); queue<int> q; q.push(0); vis[0]=1; par[0]=-1;
        while(!q.empty()){ int u=q.front();q.pop(); bfsOrder.push_back(u);
            for(int v:adj[u]) if(!vis[v]){vis[v]=1;par[v]=u;q.push(v);} }
    }
    children.assign(n,{});
    for(int i=0;i<n;i++) if(par[i]>=0) children[par[i]].push_back(i);
    // euler tour
    tin.assign(n,0); tout.assign(n,0); eulerNode.assign(n,0);
    {
        int timer=0;
        vector<pair<int,int>> stk; stk.push_back({0,0});
        while(!stk.empty()){
            auto [u,leaving]=stk.back(); stk.pop_back();
            if(leaving){ tout[u]=timer-1; }
            else {
                tin[u]=timer; eulerNode[timer]=u; timer++;
                stk.push_back({u,1});
                for(int i=(int)children[u].size()-1;i>=0;i--) stk.push_back({children[u][i],0});
            }
        }
    }
    // primes
    {
        vector<char> s(m,1);
        for(int p=2;p<m;p++){ if(!s[p])continue; primes.push_back(p); for(int q=2*p;q<m;q+=p){ s[q]=0; } }
    }
    Psize=primes.size();
    primeIdx.assign(m,-1);
    for(int i=0;i<Psize;i++) primeIdx[primes[i]]=i;

    cumshift.assign(n,0);

    // baseline objective
    ll F = computeObjective(0);
    ll Fbase = F;

    // chosen retuners
    vector<pair<int,int>> chosen; // (node, shift)
    vector<char> usedNode(n,0);
    ll retCost=0;

    // ---- Greedy: repeatedly pick best (v,d) that reduces F ----
    // Evaluating every (v,d) fully is O(n*m * eval). Too slow for big cases.
    // We restrict candidate nodes:
    //   - the root (global shift) always considered
    //   - observatory subtree roots (high-impact)
    //   - a sample of nodes
    // and for each candidate node, try all d in 1..m-1 (m<=1000).
    // Each (apply shift to subtree, eval, revert). Applying shift to subtree(v) affects
    // cumshift of all nodes in [tin,tout]. We do it in euler order quickly.

    // Build candidate node list
    auto buildCandidates=[&](int budgetNodes)->vector<int>{
        vector<int> cand;
        vector<char> seen(n,0);
        auto push=[&](int v){ if(v>=0 && v<n && !seen[v] && !usedNode[v]){ seen[v]=1; cand.push_back(v);} };
        push(0); // root
        // observatory roots, weighted: take distinct, prefer high w; collect unique
        {
            vector<pair<ll,int>> ow;
            for(int j=0;j<t;j++) ow.push_back({wObs[j], sObs[j]});
            sort(ow.rbegin(), ow.rend());
            for(auto&pr:ow){ push(pr.second); if((int)cand.size()>=budgetNodes) break; }
        }
        // fill with arbitrary nodes if room
        for(int v=0; v<n && (int)cand.size()<budgetNodes; v++) push(v);
        return cand;
    };

    // helper: apply delta shift d to subtree(v) in cumshift, over euler range
    auto applyShift=[&](int v,int d){
        int lo=tin[v], hi=tout[v];
        for(int pos=lo;pos<=hi;pos++){ int node=eulerNode[pos]; cumshift[node]=(cumshift[node]+d)%m; }
    };

    // Greedy iterations
    int iterCap = k;
    // limit total candidate evaluations by case size
    long long perStepNodeBudget;
    {
        // rough: keep nodes*m*eval bounded. eval ~ O(n log n). Want total work < ~5e8.
        // choose nodeBudget so nodeBudget * m * (n) is bounded.
        double budget = 1.2e9;
        double per = (double)m * (double)max(1,n) * 1.5; // approx eval cost
        perStepNodeBudget = (long long)max(1.0, budget/per);
        if(perStepNodeBudget>4000) perStepNodeBudget=4000;
        if(perStepNodeBudget<1) perStepNodeBudget=1;
    }

    for(int it=0; it<iterCap; it++){
        if(elapsed() > TLIM) break;
        vector<int> cand = buildCandidates((int)perStepNodeBudget);
        ll bestGain=0; int bestV=-1, bestD=0;
        bool timeUp=false;
        for(int v: cand){
            if(elapsed() > TLIM){ timeUp=true; break; }
            ll cv=c[v];
            for(int d=1; d<m; d++){
                if((d & 7)==0 && elapsed() > TLIM){ timeUp=true; break; }
                applyShift(v, +d); // tentative
                ll newF = computeObjective(retCost + cv);
                ll gain = F - newF; // positive = improvement
                applyShift(v, m-d); // revert (add (m-d) ≡ subtract d mod m)
                if(gain > bestGain){ bestGain=gain; bestV=v; bestD=d; }
            }
            if(timeUp) break;
        }
        if(bestV<0 || bestGain<=0) break;
        // commit best
        applyShift(bestV, bestD);
        usedNode[bestV]=1;
        chosen.push_back({bestV, bestD});
        retCost += c[bestV];
        F = F - bestGain;
        if((int)chosen.size() >= k) break;
    }

    // ---- Output (1-indexed nodes) ----
    // safety: ensure feasibility (distinct nodes, 1<=d<m, q<=k) — guaranteed by construction.
    {
        std::ostringstream out;
        out<<chosen.size()<<"\n";
        for(auto&pr:chosen) out<<(pr.first+1)<<" "<<pr.second<<"\n";
        cout<<out.str();
    }
    return 0;
}
