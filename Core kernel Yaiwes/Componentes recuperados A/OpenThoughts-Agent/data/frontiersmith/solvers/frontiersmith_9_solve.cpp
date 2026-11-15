// Frontiersmith 9: Duff's Defensive Lineup (heuristic)
// Minimize C(p) = sum over complaints (l,r,k) of sum_{i=l..r-1} occur(s_k, s_{p_i}+s_{p_{i+1}}).
// Baseline = identity permutation. We try a small set of candidate permutations (identity,
// reverse, sort-by-name asc/desc, sort-by-length, and random shuffles within a time budget),
// exactly evaluate each, and output the lowest-cost one (always including identity so we never
// score below baseline).
//
// Exact evaluation of a permutation:
//   For each DISTINCT target string v that appears in some complaint, compute
//   g_v[i] = occur(v, s_{p_i} + s_{p_{i+1}}) for every slot i in [0, n-2], then prefix-sum.
//   Each complaint (l,r,k) with target value v contributes PS_v[r-1] - PS_v[l-1]  (1-based slots l..r-1).
//   occur is computed with KMP; strings are tiny (|s_i|<=40, merged <=80).
#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

static int N, Q;
static vector<string> names;            // 1-based effectively; index 0..N-1
// complaints
static vector<int> cl, cr, ck;          // 0-based friend index for k; l,r are 1-based positions

// distinct target strings: map name-string -> tid; each complaint maps to a tid.
static vector<string> targets;          // distinct target strings
static vector<int> compTid;             // tid per complaint
// for each tid, list of complaints (we instead build per-tid prefix queries)

// ---- Aho-Corasick over distinct target strings ----
struct AC {
    // alphabet 26 (lowercase). nodes stored in flat arrays.
    vector<array<int,26>> go;
    vector<int> fail;
    vector<int> termTid; // -1 or a tid that ends here (each distinct target string is unique -> one tid)
    // For counting: a node may be terminal for multiple tids only if duplicate strings, but targets are distinct.
    // We also need "dictionary suffix" accumulation: matches ending here include matches via fail links.
    vector<int> dictNext; // nearest ancestor via fail that is terminal (linked list), or -1
    void build(const vector<string>& pats){
        go.clear(); fail.clear(); termTid.clear();
        go.push_back({}); go[0].fill(0); fail.push_back(0); termTid.push_back(-1);
        for(int t=0;t<(int)pats.size();t++){
            int cur=0;
            for(char ch: pats[t]){
                int c=ch-'a';
                if(go[cur][c]==0){
                    go.push_back({}); go.back().fill(0);
                    fail.push_back(0); termTid.push_back(-1);
                    go[cur][c]=(int)go.size()-1;
                }
                cur=go[cur][c];
            }
            termTid[cur]=t;
        }
        // BFS to build fail + goto automaton
        dictNext.assign(go.size(), -1);
        queue<int> bfs;
        for(int c=0;c<26;c++){ int v=go[0][c]; if(v){ fail[v]=0; bfs.push(v);} }
        while(!bfs.empty()){
            int u=bfs.front(); bfs.pop();
            // dictNext: if fail[u] terminal then fail[u] else dictNext[fail[u]]
            int f=fail[u];
            dictNext[u] = (termTid[f]>=0)? f : dictNext[f];
            for(int c=0;c<26;c++){
                int v=go[u][c];
                if(v){ fail[v]=go[f][c]; bfs.push(v); }
                else go[u][c]=go[f][c];
            }
        }
    }
};
static AC ac;

// Evaluate cost of a permutation perm (0-based friend indices, length N).
// Approach: for each slot, feed merged string s_a+s_b through AC, accumulate per-tid occurrence
// count for that slot. Then for each complaint sum its tid's g over its [l,r-1] slot range using
// per-tid prefix sums. To keep memory bounded we process tid-by-tid? No: we build, for each slot,
// the per-tid counts, but storing slots x tids is too big. Instead we accumulate into per-tid
// prefix arrays incrementally: for each slot we get a small list of (tid,count) hits (matches in
// an 80-char string is small), and we add to a running per-tid prefix structure.
// Simpler & correct: we keep psByTid[tid] as a vector of size slots+1 ONLY for tids that have
// complaints, lazily. But that is D*slots memory again (~2000*2000*8=32MB) — acceptable < 512MB.
// psByTid[t] is a prefix-sum array of length slots+1 (only allocated for complaint-tids):
//   psByTid[t][i] = sum over slots 1..i (1-based) of occur(target_t, merged at that slot).
// Built by first accumulating per-slot DELTAS into the array, then a single prefix pass.
static vector<vector<ll>> psByTid;
static vector<char> hasComp; // tid -> has complaints
static ll evalCost(const vector<int>& perm,
                   const vector<vector<int>>& tidComplaints,
                   string& merged){
    int slots=N-1;
    if(slots<=0) return 0;
    int D=(int)targets.size();
    // zero the delta arrays (length slots+1) for complaint-tids
    for(int t=0;t<D;t++){
        if(!hasComp[t]) continue;
        auto& v=psByTid[t];
        if((int)v.size()!=slots+1) v.assign(slots+1,0);
        else std::fill(v.begin(),v.end(),0);
    }
    // accumulate deltas: for slot sI (0-based), occurrences land at index sI+1
    for(int sI=0; sI<slots; sI++){
        int a=perm[sI], b=perm[sI+1];
        merged.clear(); merged+=names[a]; merged+=names[b];
        int node=0;
        for(char ch: merged){
            node=ac.go[node][ch-'a'];
            int u=node;
            int t0=ac.termTid[u];
            if(t0>=0 && hasComp[t0]) psByTid[t0][sI+1]++;
            int d=ac.dictNext[u];
            while(d>=0){ int t=ac.termTid[d]; if(t>=0 && hasComp[t]) psByTid[t][sI+1]++; d=ac.dictNext[d]; }
        }
    }
    // prefix-sum each complaint-tid array, then sum complaint contributions
    ll total=0;
    for(int t=0;t<D;t++){
        if(!hasComp[t]) continue;
        auto& v=psByTid[t];
        for(int i=1;i<=slots;i++) v[i]+=v[i-1];
        for(int ci: tidComplaints[t]){ int l=cl[ci], r=cr[ci]; total += v[r-1]-v[l-1]; }
    }
    return total;
}

int main(){
    auto t0 = chrono::steady_clock::now();
    // fast input
    static char ibuf[1<<25];
    int rd = fread(ibuf,1,sizeof(ibuf),stdin);
    int total = rd; string extra;
    while(rd==(int)sizeof(ibuf)){
        string more; more.resize(1<<25);
        rd = fread(&more[0],1,more.size(),stdin);
        extra.append(more.data(), rd);
        total += rd;
    }
    string data; data.reserve(total);
    data.append(ibuf, (size_t)min(total,(int)sizeof(ibuf)));
    if(total>(int)sizeof(ibuf)) data.append(extra);
    const char* s=data.data(); const char* end=s+data.size();
    auto readInt=[&]()->ll{
        while(s<end && (*s<'0'||*s>'9') && *s!='-') s++;
        bool neg=false; if(s<end && *s=='-'){neg=true;s++;}
        ll v=0; while(s<end && *s>='0'&&*s<='9'){ v=v*10+(*s-'0'); s++; }
        return neg?-v:v;
    };
    auto readWord=[&](string& out){
        out.clear();
        while(s<end && (*s==' '||*s=='\n'||*s=='\r'||*s=='\t')) s++;
        while(s<end && *s>='a' && *s<='z'){ out+=*s; s++; }
    };

    N=(int)readInt(); Q=(int)readInt();
    names.resize(N);
    for(int i=0;i<N;i++) readWord(names[i]);
    cl.resize(Q); cr.resize(Q); ck.resize(Q);
    for(int j=0;j<Q;j++){
        cl[j]=(int)readInt(); cr[j]=(int)readInt();
        int k=(int)readInt(); ck[j]=k-1; // 0-based friend index
    }

    // distinct target strings used in complaints
    unordered_map<string,int> tmap; tmap.reserve(Q*2);
    compTid.resize(Q);
    for(int j=0;j<Q;j++){
        const string& nm = names[ck[j]];
        auto it=tmap.find(nm);
        int tid;
        if(it==tmap.end()){ tid=(int)targets.size(); tmap.emplace(nm,tid); targets.push_back(nm); }
        else tid=it->second;
        compTid[j]=tid;
    }
    // tid -> complaint indices
    vector<vector<int>> tidComplaints(targets.size());
    for(int j=0;j<Q;j++) tidComplaints[compTid[j]].push_back(j);

    // build Aho-Corasick over distinct targets
    ac.build(targets);
    int D=(int)targets.size();
    hasComp.assign(D,0);
    psByTid.assign(D, {});
    for(int t=0;t<D;t++) if(!tidComplaints[t].empty()) hasComp[t]=1;

    // candidate permutations
    vector<int> identity(N); for(int i=0;i<N;i++) identity[i]=i;

    string merged; merged.reserve(96);

    // best so far = identity
    vector<int> best = identity;
    ll bestCost = evalCost(identity, tidComplaints, merged);

    auto consider=[&](vector<int>& cand){
        ll c = evalCost(cand, tidComplaints, merged);
        if(c < bestCost){ bestCost=c; best=cand; }
    };

    auto elapsed=[&]()->double{
        return chrono::duration<double>(chrono::steady_clock::now()-t0).count();
    };

    const double TIME_LIMIT = 3.6; // seconds, safely under 5s; checked before each eval (one eval ~0.5s)

    // candidate: reverse
    if(elapsed()<TIME_LIMIT){
        vector<int> rev(identity.rbegin(), identity.rend());
        consider(rev);
    }
    // candidate: sort by name asc
    if(elapsed()<TIME_LIMIT){
        vector<int> byName=identity;
        sort(byName.begin(),byName.end(),[&](int a,int b){ return names[a]<names[b]; });
        consider(byName);
        // desc
        if(elapsed()<TIME_LIMIT){
            vector<int> byNameD(byName.rbegin(), byName.rend());
            consider(byNameD);
        }
    }
    // candidate: sort by length asc/desc
    if(elapsed()<TIME_LIMIT){
        vector<int> byLen=identity;
        sort(byLen.begin(),byLen.end(),[&](int a,int b){ if(names[a].size()!=names[b].size()) return names[a].size()<names[b].size(); return names[a]<names[b]; });
        consider(byLen);
    }

    // random shuffles within remaining time budget
    std::mt19937 rng(12345);
    while(elapsed()<TIME_LIMIT){
        vector<int> cand=identity;
        shuffle(cand.begin(),cand.end(),rng);
        consider(cand);
        // also try a local-improvement style: based on best, swap a few random pairs
        if(elapsed()>=TIME_LIMIT) break;
        vector<int> cand2=best;
        for(int t=0;t<8;t++){
            int i=rng()%N, j=rng()%N; std::swap(cand2[i],cand2[j]);
        }
        consider(cand2);
    }

    // output best permutation (1-based)
    string out; out.reserve((size_t)N*7+8);
    for(int i=0;i<N;i++){ out += to_string(best[i]+1); out += (i+1<N?' ':'\n'); }
    fwrite(out.data(),1,out.size(),stdout);
    return 0;
}
