#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
typedef complex<double> cd;
static const double PI = acos(-1.0);

void fft(vector<cd>& a, bool invert) {
    int n = (int)a.size();
    for (int i = 1, j = 0; i < n; i++) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) swap(a[i], a[j]);
    }
    for (int len = 2; len <= n; len <<= 1) {
        double ang = 2.0 * PI / len * (invert ? -1 : 1);
        cd wlen(cos(ang), sin(ang));
        for (int i = 0; i < n; i += len) {
            cd w(1);
            for (int j = 0; j < len / 2; j++) {
                cd u = a[i+j], v = a[i+j+len/2]*w;
                a[i+j] = u+v; a[i+j+len/2] = u-v;
                w *= wlen;
            }
        }
    }
    if (invert) for (auto& x : a) x /= n;
}

// cyclic convolution of indicator A with B = (1-A), counts c_r
// returns objective sum w_r * min(c_r, d_r)
// Uses FFT. For small M uses direct O(M^2).
int M;
vector<ll> W, D;
int Nfft;
vector<cd> base_fb_ones; // not used

ll objFromA(const vector<char>& A) {
    int sizeA = 0;
    for (int i = 0; i < M; i++) sizeA += A[i];
    if (sizeA == 0 || sizeA == M) return 0;
    vector<ll> c(M, 0);
    if ((ll)M * M <= 4000000LL) {
        // direct
        // c_r = sum over a in A, b in B with (a+b)%M==r
        // count B residues
        vector<int> bcnt(M);
        for (int i = 0; i < M; i++) bcnt[i] = (A[i] ? 0 : 1);
        for (int a = 0; a < M; a++) if (A[a]) {
            for (int b = 0; b < M; b++) if (!A[b]) {
                int r = a + b; if (r >= M) r -= M;
                c[r]++;
            }
        }
    } else {
        vector<cd> fa(Nfft, 0), fb(Nfft, 0);
        for (int i = 0; i < M; i++) { fa[i] = A[i]?1.0:0.0; fb[i] = A[i]?0.0:1.0; }
        fft(fa, false); fft(fb, false);
        for (int i = 0; i < Nfft; i++) fa[i] *= fb[i];
        fft(fa, true);
        for (int i = 0; i < 2*M-1; i++) c[i % M] += (ll)llround(fa[i].real());
    }
    ll total = 0;
    for (int r = 0; r < M; r++) total += W[r] * min(c[r], D[r]);
    return total;
}

int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    ll B;
    if(!(cin >> M >> B)) return 0;
    vector<ll> cost(M);
    for (int i=0;i<M;i++) cin>>cost[i];
    W.resize(M); D.resize(M);
    for (int i=0;i<M;i++) cin>>W[i];
    for (int i=0;i<M;i++) cin>>D[i];

    Nfft = 1; while (Nfft < 2*M) Nfft <<= 1;

    // order by cost asc, tie by index
    vector<int> order(M); iota(order.begin(),order.end(),0);
    sort(order.begin(),order.end(),[&](int a,int b){
        return cost[a]<cost[b] || (cost[a]==cost[b] && a<b);
    });
    // prefix: max ports affordable = the baseline-style fill
    // affordable counts: greedily how many cheapest we can take
    int maxAff = 0; ll spent=0;
    for (int idx: order){ if (cost[idx] <= B - spent){ spent+=cost[idx]; maxAff++; } else break; }
    // maxAff = number we can take if we take cheapest contiguous. (since sorted, once one fails cheaper-prefix logic: actually a later cheaper? no sorted asc so prefix is optimal count)
    // But budget check must be exact per-port; recompute prefix sums
    // Build best solution by trying various target sizes t (cheapest t ports), 0<t<M, t<=maxAff
    if (maxAff >= M) maxAff = M; // can't exceed
    // We need B nonempty so t < M. cap t at M-1.
    int tcap = min(maxAff, M-1);
    if (tcap < 1) {
        // can only afford <1? guaranteed at least one port affordable, so maxAff>=1
        tcap = min(maxAff, M-1);
    }

    // candidate t values: a set spread over [1, tcap]
    vector<int> cand;
    auto addc=[&](int t){ if(t>=1 && t<=tcap) cand.push_back(t); };
    // log-spaced + linear-ish
    for (int t=1; t<=tcap && t<=64; t++) addc(t);
    for (int frac=1; frac<200; frac++){ addc((ll)tcap*frac/200); }
    addc(tcap); addc(tcap/2); addc(tcap/3); addc(2*tcap/3); addc(tcap/4); addc(3*tcap/4);
    addc(min(tcap, M/2)); addc(min(tcap, M/3)); addc(min(tcap,(int)(M*2/3)));
    sort(cand.begin(),cand.end()); cand.erase(unique(cand.begin(),cand.end()),cand.end());

    // Limit number of FFT evaluations for very large M to stay in time.
    int maxEvals;
    if (M <= 2000) maxEvals = 1000000; // direct or cheap
    else if (M <= 20000) maxEvals = 400;
    else if (M <= 100000) maxEvals = 120;
    else maxEvals = 60;
    if ((int)cand.size() > maxEvals) {
        // subsample evenly
        vector<int> c2;
        double step = (double)cand.size()/maxEvals;
        for (int i=0;i<maxEvals;i++){ int idx=(int)(i*step); if(idx<(int)cand.size()) c2.push_back(cand[idx]); }
        c2.push_back(cand.back());
        sort(c2.begin(),c2.end()); c2.erase(unique(c2.begin(),c2.end()),c2.end());
        cand=c2;
    }

    ll bestObj = -1; int bestT = 1;
    vector<char> A(M,0);
    // For each t, take cheapest t ports
    for (int t : cand) {
        // build A = first t in order
        fill(A.begin(),A.end(),0);
        for (int i=0;i<t;i++) A[order[i]]=1;
        ll obj = objFromA(A);
        if (obj > bestObj){ bestObj=obj; bestT=t; }
    }

    // Final A from best cheapest-prefix
    fill(A.begin(),A.end(),0);
    for (int i=0;i<bestT;i++) A[order[i]]=1;
    ll curObj = bestObj;
    ll curCost = 0; for(int i=0;i<M;i++) if(A[i]) curCost+=cost[i];

    // ---- Local search: swap/add/remove to improve objective within budget ----
    // Bounded by wall clock. Each move re-evaluates objective via objFromA.
    auto t0 = chrono::steady_clock::now();
    double timeBudget = (M <= 2000) ? 5.0 : (M <= 20000 ? 3.0 : 0.0);
    // For very large M, FFT per move is too costly; skip local search.
    std::mt19937 rng(12345);
    // Deterministic exhaustive single-swap hill climb for small M.
    if (M <= 400 && M >= 2) {
        bool improved = true;
        while (improved) {
            double el = chrono::duration<double>(chrono::steady_clock::now()-t0).count();
            if (el > timeBudget) break;
            improved = false;
            for (int inP=0; inP<M; inP++) if (A[inP]) {
                for (int outP=0; outP<M; outP++) if (!A[outP]) {
                    ll nc = curCost - cost[inP] + cost[outP];
                    if (nc > B) continue;
                    A[inP]=0; A[outP]=1;
                    ll no = objFromA(A);
                    if (no > curObj) { curObj=no; curCost=nc; improved=true; }
                    else { A[inP]=1; A[outP]=0; }
                }
                double e2 = chrono::duration<double>(chrono::steady_clock::now()-t0).count();
                if (e2 > timeBudget) { improved=false; break; }
            }
            // also try add and remove sweeps
            for (int x=0;x<M && curObj>=0;x++){
                if(!A[x] && curCost+cost[x]<=B){ int outc=0;for(int i=0;i<M;i++)if(!A[i])outc++; if(outc<=1)break; A[x]=1; ll no=objFromA(A); if(no>curObj){curObj=no;curCost+=cost[x];improved=true;} else A[x]=0; }
            }
            for (int x=0;x<M;x++){ int sz=0;for(int i=0;i<M;i++)sz+=A[i]; if(sz<=1)break; if(A[x]){ A[x]=0; ll no=objFromA(A); if(no>curObj){curObj=no;curCost-=cost[x];improved=true;} else A[x]=1; } }
        }
        bestObj = max(bestObj, curObj);
    }
    if (timeBudget > 0 && M >= 2) {
        vector<char> bestA = A;
        while (true) {
            double el = chrono::duration<double>(chrono::steady_clock::now()-t0).count();
            if (el > timeBudget) break;
            // pick a random move type
            int mt = rng()%3;
            int idx;
            if (mt==0) {
                // swap: remove a random in-port, add a random out-port
                // find an in port
                int inP=-1, outP=-1;
                for (int tries=0; tries<8 && inP<0; tries++){ int x=rng()%M; if(A[x]) inP=x; }
                for (int tries=0; tries<8 && outP<0; tries++){ int x=rng()%M; if(!A[x]) outP=x; }
                if (inP<0||outP<0) continue;
                ll nc = curCost - cost[inP] + cost[outP];
                if (nc > B) continue;
                A[inP]=0; A[outP]=1;
                ll no = objFromA(A);
                if (no >= curObj) { curObj=no; curCost=nc; if(no>bestObj){bestObj=no;bestA=A;} }
                else { A[inP]=1; A[outP]=0; }
            } else if (mt==1) {
                // add an out-port if affordable and keeps B nonempty
                { int outc=0; for(int i=0;i<M;i++) if(!A[i]) outc++; if(outc<=1) continue; }
                for (int tries=0;tries<8;tries++){ int x=rng()%M; if(!A[x] && curCost+cost[x]<=B){ A[x]=1; ll no=objFromA(A); if(no>=curObj){curObj=no;curCost+=cost[x]; if(no>bestObj){bestObj=no;bestA=A;}} else A[x]=0; break; } }
            } else {
                // remove an in-port (keep A nonempty)
                int sz=0; for(int i=0;i<M;i++) sz+=A[i]; if(sz<=1) continue;
                for (int tries=0;tries<8;tries++){ int x=rng()%M; if(A[x]){ A[x]=0; ll no=objFromA(A); if(no>=curObj){curObj=no;curCost-=cost[x]; if(no>bestObj){bestObj=no;bestA=A;}} else A[x]=1; break; } }
            }
        }
        A = bestA;
    }
    // verify budget
    ll tc=0; for(int i=0;i<M;i++) if(A[i]) tc+=cost[i];
    if (tc > B) { // safety fallback to cheapest-prefix
        fill(A.begin(),A.end(),0);
        for (int i=0;i<bestT;i++) A[order[i]]=1;
    }

    // collect ports sorted increasing
    vector<int> ports;
    for (int i=0;i<M;i++) if(A[i]) ports.push_back(i);
    // output
    string out; out.reserve(ports.size()*7+16);
    out += to_string((int)ports.size()); out += '\n';
    for (size_t i=0;i<ports.size();i++){ out += to_string(ports[i]); out += (i+1<ports.size()?' ':'\n'); }
    if (ports.empty()) out += '\n';
    fputs(out.c_str(), stdout);
    return 0;
}
