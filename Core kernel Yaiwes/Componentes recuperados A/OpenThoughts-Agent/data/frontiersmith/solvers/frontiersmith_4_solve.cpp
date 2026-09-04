#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
static const ll INF = (ll)4e18;

int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n,m,k;
    if(!(cin>>n>>m>>k)) return 0;
    vector<int> X(m+1), Y(m+1);
    vector<ll> C(m+1);
    // adjacency: store (neighbor, weight, signed trail id to go this direction)
    vector<vector<tuple<int,ll,int>>> adj(n+1);
    for (int i=1;i<=m;i++){
        cin>>X[i]>>Y[i]>>C[i];
        // from X to Y via +i ; from Y to X via -i
        adj[X[i]].push_back({Y[i], C[i], i});
        if (X[i]!=Y[i]) adj[Y[i]].push_back({X[i], C[i], -i});
    }
    // Dijkstra from 1, record parent signed trail to reach node v from its parent
    vector<ll> dist(n+1, INF);
    vector<int> parTrail(n+1, 0); // signed trail used to arrive at v (from parent->v)
    dist[1]=0;
    priority_queue<pair<ll,int>, vector<pair<ll,int>>, greater<pair<ll,int>>> pq;
    pq.push({0,1});
    while(!pq.empty()){
        auto [d,u]=pq.top(); pq.pop();
        if(d>dist[u]) continue;
        for(auto &e: adj[u]){
            int v=get<0>(e); ll w=get<1>(e); int sid=get<2>(e);
            if(dist[u]+w<dist[v]){
                dist[v]=dist[u]+w;
                parTrail[v]=sid; // to go u->v use sid (u is parent of v)
                pq.push({dist[v],v});
            }
        }
    }

    // Build path from 1 to v as a list of signed trail ids (in order from 1 to v).
    // We need parent node too; derive parent from the signed trail: if sid>0, edge i goes X->Y,
    // so arriving at v=Y means parent = X. if sid<0, edge |sid| goes Y->X, arriving at v=X, parent=Y.
    auto parentOf=[&](int v)->int{
        int sid=parTrail[v];
        if(sid==0) return -1; // root or unreachable
        int e=abs(sid);
        if(sid>0) return X[e]; else return Y[e];
    };

    // path1to(v): vector of signed trail ids from node 1 to v
    // We'll build by walking up to root then reversing.
    auto path1to=[&](int v, vector<int>&out){
        out.clear();
        int cur=v;
        while(cur!=1 && parTrail[cur]!=0){
            out.push_back(parTrail[cur]); // this step goes parent->cur
            cur=parentOf(cur);
            if(cur<0) break;
        }
        reverse(out.begin(), out.end()); // now from 1 to v
    };

    // tau for each trail and greedy balancing assignment (mirror baseline)
    vector<ll> tau(m+1);
    for(int i=1;i<=m;i++){
        ll dx=dist[X[i]], dy=dist[Y[i]];
        tau[i] = (dx>=INF||dy>=INF)? INF : dx + C[i] + dy;
    }
    vector<int> order(m);
    iota(order.begin(),order.end(),1);
    sort(order.begin(),order.end(),[&](int a,int b){
        if(tau[a]!=tau[b]) return tau[a]>tau[b];
        return a<b;
    });

    // Assign trails to teams greedily by least current load (load measured by tau, like baseline)
    vector<ll> load(k,0);
    vector<vector<int>> teamTrails(k);
    for(int idx: order){
        int best=0;
        for(int j=1;j<k;j++) if(load[j]<load[best]) best=j;
        load[best]+=tau[idx];
        teamTrails[best].push_back(idx);
    }

    // For each team, build a closed walk.
    // Strategy: merge per-trail round trips that share tree-path prefixes.
    // Walk for trail i (as standalone) = path(1->x_i) + [+i] + reverse(path(1->y_i))
    //   where reverse path uses negated ids in reverse order.
    // To reduce travel: order a team's trails so that we descend once and service nearby trails.
    // SIMPLE-AND-SAFE improvement: for each team, sort its trails, then build a single walk:
    //   we maintain current node = 1. For each trail (sorted to group by descent), we travel from
    //   current node to x_i along: go up to root, then down to x_i. To keep it simple & always feasible,
    //   we go current->1 (reverse current path) then 1->x_i. But we don't track current path easily.
    // Instead: standalone round trips concatenated. This EXACTLY reproduces baseline cost. Then we
    // apply a local merge: consecutive trails sharing a common ancestor chain skip re-walking shared prefix.
    //
    // We implement the merged DFS-style walk per team for genuine improvement:
    //   Collect endpoints; do per-trail out-and-back but reuse a shared "spine" to the deepest common point.
    // For robustness we implement: concatenate, for each trail, path(1->near) + serve + back, where for the
    // trail we go near->far via trail then far->near via trail (2*c) only if cheaper than via tree; else
    // near->far->(tree back to near). Simplicity: near=endpoint with smaller dist.
    //
    // To guarantee improvement w.r.t. baseline AND feasibility, use this per-trail walk:
    //   let a=endpoint with smaller dist, b=other. walk = path(1->a) + [trail a->b] + [trail b->a] + path(a->1)
    //   cost = dist(a) + c + c + dist(a) = 2*dist(a) + 2*c.
    //   baseline τ = dist(a)+dist(b)+c. Our per-trail cost 2dist(a)+2c. Not always better.
    // So instead reproduce baseline exactly per trail: path(1->x)+[+i]+path(y->1), cost = dist(x)+c+dist(y)=τ.
    // Then MERGE within team to share prefixes => strictly <= baseline.

    // Build output. We construct each team's walk as a sequence of signed ids.
    // Merge approach: for a team, we process its trails; we keep the walk as: starting at 1,
    // for each trail we APPEND path(1->x_i)+[+i]+path(y_i->1). That's baseline cost (sum tau). Feasible: each
    // sub-walk starts and ends at 1, so concatenation is a valid closed walk from 1.
    // Then we post-merge: when one sub-walk ends with "...->1" and next begins "1->...", and they share a
    // common prefix of tree edges from 1, we cancel the round trip on the shared prefix (go down once,
    // service both, come up once). We do a generic optimization below.

    // For simplicity and guaranteed feasibility we emit baseline-equivalent concatenation, which yields
    // A <= B (== B), score ratio >= 0.5. We additionally apply prefix-merge to beat baseline.

    // Precompute path(1->v) lazily with cache for endpoints we need.
    // For large m this is fine: total path length sum could be large but bounded by tree depth * m.
    // To bound memory/time, we DO NOT materialize all paths; we build each team's walk by a tree DFS.

    // ---- Tree-DFS per team (true improvement) ----
    // Build children adjacency of the SP tree.
    // child edges: for v!=1 with parTrail[v]!=0, parent = parentOf(v), edge signed parTrail[v] (parent->v).
    vector<vector<int>> childNode(n+1);     // children nodes
    vector<int> childSid; // not needed separately; recompute via parTrail[child]
    for(int v=1; v<=n; v++){
        if(v==1) continue;
        if(parTrail[v]==0) continue;
        int p=parentOf(v);
        if(p>=1 && p<=n) childNode[p].push_back(v);
    }

    // For each team: we have a set of trails. We need to traverse each once and return to 1.
    // Required tree nodes = union of all endpoints of assigned trails plus path to root.
    // We do an iterative DFS from 1 over tree edges that are "needed" (lie on path to some required node).
    // At each node, after entering (descended via its parent edge), we service trails whose chosen
    // service-point is this node, then descend to needed children, then ascend.
    // Servicing a trail i at node x (one of its endpoints): traverse +/-i to the other endpoint and back.
    //   pick service endpoint = x_i (we go from x_i: x_i->y_i->x_i). signed: if at x_i, use +i then -i.
    //   if self-loop (x==y): just +i (then we're back at x). cost c. covered.
    // This guarantees: each trail traversed (covered), team starts & ends at 1.
    // Cost per team = 2*(sum of needed tree edge weights) + sum over trails(2*c_i) [or c_i for self-loop
    //   serviced where it returns]. Actually x_i->y_i->x_i costs 2*c_i.
    // Shared tree descent => beats baseline when trails share ancestry.

    // Choose service node for each trail = the endpoint with SMALLER dist (closer to root) to minimize
    // needed tree edges; mark needed nodes accordingly. We must ensure that endpoint is reachable (it is).

    // Mark needed nodes per team and assign trail service lists.
    // We process teams independently. To bound total cost, note sum of needed tree edges per team <= tree size.

    string outbuf;
    outbuf.reserve(1<<20);

    // helper: build path of signed ids from ancestor root(1) down to node v (we already have path1to)
    // We'll do explicit DFS using childNode but only visiting needed nodes.
    vector<char> needed(n+1, 0);
    vector<vector<int>> serviceAt(n+1); // trails to service at this node (store signed: at endpoint with smaller dist)
    vector<int> touchedNodes; touchedNodes.reserve(1024);

    // reuse parentEdgeSigned: to go parent->v use parTrail[v]; v->parent use -parTrail[v]
    // iterative DFS stack frame
    vector<int> walk; walk.reserve(1<<16);

    // path cache for baseline-style walk construction
    vector<int> tmpPath;
    auto buildBaselineWalk=[&](const vector<int>& trails, vector<int>& w)->ll{
        w.clear();
        ll cost=0;
        for(int i: trails){
            // path(1->x_i) + [+i] + path(y_i->1)
            path1to(X[i], tmpPath);
            for(int s: tmpPath) w.push_back(s);
            w.push_back(i);
            path1to(Y[i], tmpPath);
            for(int t2=(int)tmpPath.size()-1; t2>=0; t2--) w.push_back(-tmpPath[t2]);
            cost += dist[X[i]] + C[i] + dist[Y[i]];
        }
        return cost;
    };

    for(int j=0;j<k;j++){
        if(teamTrails[j].empty()){
            outbuf += "0\n";
            continue;
        }
        // mark needed nodes
        touchedNodes.clear();
        // For each trail, choose service endpoint (smaller dist), mark path to root.
        for(int i: teamTrails[j]){
            int sx=X[i], sy=Y[i];
            int sv; int sid; // service: from sv traverse to other and back
            if(sx==sy){
                sv=sx; sid=i; // self loop: +i returns to sx
            } else {
                if(dist[sx]<=dist[sy]){ sv=sx; sid=i; } // at sx, +i goes sx->sy
                else { sv=sy; sid=-i; } // at sy, -i goes sy->sx
            }
            serviceAt[sv].push_back(sid);
            if(!needed[sv]){ /*marking nodes on path below*/ }
            // mark path from sv up to root
            int cur=sv;
            while(cur!=-1 && !needed[cur]){
                needed[cur]=1; touchedNodes.push_back(cur);
                if(cur==1) break;
                cur=parentOf(cur);
            }
        }
        // iterative DFS from node 1 over needed children
        walk.clear();
        // stack of (node, childIndex)
        // We'll push entries; on first visit we don't add an edge (we entered via parent already except root)
        // Manage manually.
        struct Frame{int node; size_t ci;};
        vector<Frame> st;
        // enter root: service root's trails
        // service function appends signed ids; for trail at node v service = [sid, -sid] (out and back),
        // except self-loop where it's just [sid].
        auto serviceNode=[&](int v){
            for(int sid: serviceAt[v]){
                int e=abs(sid);
                if(X[e]==Y[e]){ walk.push_back(sid); } // self loop, returns to v
                else { walk.push_back(sid); walk.push_back(-sid); }
            }
        };
        st.push_back({1,0});
        serviceNode(1);
        while(!st.empty()){
            Frame &f=st.back();
            // find next needed child not yet visited
            bool descended=false;
            while(f.ci < childNode[f.node].size()){
                int c=childNode[f.node][f.ci];
                f.ci++;
                if(needed[c]){
                    // descend: edge parent->c is parTrail[c]
                    walk.push_back(parTrail[c]);
                    serviceNode(c);
                    st.push_back({c,0});
                    descended=true;
                    break;
                }
            }
            if(descended) continue;
            // done with this node: ascend (unless root)
            int v=f.node;
            st.pop_back();
            if(!st.empty()){
                // go back to parent: edge v->parent = -parTrail[v]
                walk.push_back(-parTrail[v]);
            }
        }
        // compute DFS walk cost
        ll dfsCost=0; for(int s: walk) dfsCost += C[abs(s)];
        // baseline-style cost for this team == sum tau == load[j] (computed earlier)
        ll baseCost = load[j];
        static vector<int> baseWalk;
        const vector<int>* chosen;
        if(dfsCost <= baseCost){
            chosen = &walk;
        } else {
            // DFS worse: emit baseline-equivalent walk (only built when actually needed)
            buildBaselineWalk(teamTrails[j], baseWalk);
            chosen = &baseWalk;
        }
        // emit
        outbuf += to_string((int)chosen->size());
        for(int s: *chosen){ outbuf += ' '; outbuf += to_string(s); }
        outbuf += '\n';
        // cleanup marks
        for(int nd: touchedNodes){ needed[nd]=0; serviceAt[nd].clear(); }
    }

    fputs(outbuf.c_str(), stdout);
    return 0;
}
