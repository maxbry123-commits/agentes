
#!/usr/bin/env python3
"""
Multiverse
==========
A "Universe" that holds multiple WorldModel episodes under a single top-level node,
and can derive focused retrieval graphs for agent decision-making.

Provided views (built purely from per-episode task_data):
  1) COG  - Commitment-Outcome Graph: (task, time bucket, team size k) -> success metrics
  2) TCG  - Template-Context Graph:   (task, bucket, k, comms, template) -> success metrics
  3) PDG  - Plan-Delta Graph:         pairwise template improvements per context
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx

from world_model import WorldModel


@dataclass
class EpisodeRecord:
    episode_id: str
    wm: WorldModel
    anchor_pos: Tuple[float, float] = (0.0, 0.0)


@dataclass
class MultiverseStats:
    num_episodes: int = 0
    episodes_completed: int = 0
    episode_min_time: Optional[int] = None
    episode_max_time: Optional[int] = None
    episode_avg_time: Optional[float] = None
    task_stats: Dict[str, Dict] = field(default_factory=dict)


class Multiverse:
    def __init__(self, name: str = 'UNIVERSE'):
        self.name = name
        self.universe_graph: Optional[nx.Graph] = None
        self.episodes: Dict[str, EpisodeRecord] = {}
        self.node_positions: Dict[str, Tuple[float, float]] = {}
        self.node_labels: Dict[str, str] = {}
        self.node_colors: List[str] = []
        self.node_sizes: List[int] = []
        self.stats = MultiverseStats()
        self.views: Dict[str, dict] = {}

    # ------------------------------
    # Public API
    # ------------------------------
    def add_world_model(self, wm_or_path: Union[WorldModel, str, Path], episode_id: Optional[str] = None):
        """Add a WorldModel (or path to its JSON export) to the universe; rebuild aggregates and graph."""
        if isinstance(wm_or_path, (str, Path)):
            wm = WorldModel(str(wm_or_path))
            wm.parse_log()
        else:
            wm = wm_or_path
            if wm.graph is None:
                wm.parse_log()

        if episode_id is None:
            episode_id = f"E{len(self.episodes)+1}"
        if episode_id in self.episodes:
            raise ValueError(f"Episode id '{episode_id}' already exists.")

        self.episodes[episode_id] = EpisodeRecord(episode_id=episode_id, wm=wm)
        self._recompute_aggregates()
        self._build_universe_graph()

    def visualize(self, save_path: str = 'universe_graph.png', show_plot: bool = True):
        if self.universe_graph is None:
            raise ValueError("Universe graph not built.")
        plt.figure(figsize=(28, 22))

        U = self._universe_node_id()
        pos = nx.spring_layout(self.universe_graph, pos=self.node_positions, k=2, iterations=10, fixed=[U])
        for n, p in pos.items():
            self.node_positions[n] = p

        nx.draw_networkx_nodes(self.universe_graph, self.node_positions,
                               node_color=self.node_colors, node_size=self.node_sizes, alpha=0.85)
        nx.draw_networkx_edges(self.universe_graph, self.node_positions, edge_color='gray', alpha=0.6, width=1.0)

        # Dotted overlap edges between instance (leaf) nodes with overlapping time within each episode
        try:
            overlap_edges = self._compute_overlap_edges()
        except Exception:
            overlap_edges = []
        if overlap_edges:
            nx.draw_networkx_edges(
                self.universe_graph, self.node_positions,
                edgelist=overlap_edges, style='dotted', alpha=0.5, width=1.2, edge_color='black')

        ux, uy = self.node_positions[U]
        plt.text(ux, uy, self.node_labels[U], fontsize=16, ha='center', va='center', fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.6", facecolor="white", alpha=0.97, edgecolor="black", linewidth=2.2))

        ep_labels = {n: l for n, l in self.node_labels.items()
                     if self.universe_graph.nodes[n].get('node_type') == 'episode'}
        nx.draw_networkx_labels(self.universe_graph, self.node_positions, ep_labels, font_size=12, font_weight='bold')

        for n, l in self.node_labels.items():
            typ = self.universe_graph.nodes[n].get('node_type')
            if typ in ('task', 'template', 'instance'):
                x, y = self.node_positions[n]
                fs = 10 if typ == 'task' else (8 if typ == 'template' else 6)
                plt.text(x, y, l, fontsize=fs, ha='center', va='center',
                         bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.88, edgecolor="black"))

        plt.title('Multiverse Graph: Universe → Episodes → Tasks → Templates → Instances',
                  fontsize=18, fontweight='bold', pad=22)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        if show_plot:
            plt.show()
        else:
            plt.close()
        return save_path

    def export_graph(self, save_path: str = 'universe_graph.json'):
        if self.universe_graph is None:
            raise ValueError("Universe graph not built.")
        graph_dict = nx.node_link_data(self.universe_graph)
        graph_dict['universe_data'] = {
            'name': self.name,
            'stats': self._stats_dict(),
            'episodes': {
                eid: {
                    'episode_data': rec.wm.episode_data,
                    'task_data': rec.wm.task_data,
                    'node_positions': rec.wm.node_positions,
                    'node_labels': rec.wm.node_labels,
                }
                for eid, rec in self.episodes.items()
            },
            'views': getattr(self, 'views', {})
        }
        with open(save_path, 'w') as f:
            json.dump(graph_dict, f, indent=2, default=str)
        return save_path

    # ------------------------------
    # Focused Retrieval Views
    # ------------------------------
    def build_views(self, bucket: int = 10):
        """
        Build three compact retrieval graphs from in-memory episode data only:
          1) COG  - Commitment-Outcome Graph
          2) TCG  - Template-Context Graph
          3) PDG  - Plan-Delta Graph (pairwise template improvements per context)
        Returns a dict and also stores it on self.views
        """
        instances = self._collect_instances()
        cog, kstar = self._build_cog(instances, bucket)
        tcg = self._build_tcg(instances, bucket)
        pdg = self._build_pdg(tcg)
        self.views = {"COG": cog, "COG_kstar": kstar, "TCG": tcg, "PDG": pdg}
        return self.views

    def _collect_instances(self):
        """Extract minimal per-instance records from each episode's task_data.
        Relies only on fields present in universe_graph.json's per-episode task_data.
        """
        out = []
        for eid, rec in self.episodes.items():
            tdata = rec.wm.task_data or {}
            for task, td in tdata.items():
                templates = (td or {}).get('templates', {})
                for tpl_name, tpl in templates.items():
                    for inst in tpl.get('instances', []):
                        commits = inst.get('all_agents_commitments', {}) or {}
                        k = sum(1 for v in commits.values() if v == task)
                        plan = inst.get('plan', []) or []
                        plan_tokens = [a.split()[0] if isinstance(a, str) else str(a) for a in plan]
                        out.append({
                            'episode_id': eid,
                            'task': task,
                            'template': tpl_name,
                            'start_step': inst.get('start_step'),
                            'success': inst.get('success'),
                            'end_step': inst.get('end_step'),
                            'comms': inst.get('communication_type'),
                            'k': int(k or 1),
                            'plan_tokens': plan_tokens,
                        })
        return out

    @staticmethod
    def _bucketize(step: int, bucket: int) -> str:
        if step is None:
            return "unknown"
        b = (step // bucket) * bucket
        return f"{b}-{b+bucket}"

    def _build_cog(self, instances, bucket: int):
        """Commitment-Outcome Graph and k* per (task,bucket).
        Keys: "task|bucket|k" -> metrics
        """
        from collections import defaultdict
        def key(task, b, k):
            return f"{task}|bucket={b}|k={k}"
        agg = defaultdict(lambda: {'attempts':0,'successes':0,'avg_t':None,'min_t':None,'max_t':None,'comms':{}})
        per_tb = defaultdict(list)

        for inst in instances:
            b = self._bucketize(inst['start_step'], bucket)
            k = inst['k']
            kkey = key(inst['task'], b, k)
            m = agg[kkey]
            m['attempts'] += 1
            if inst['success'] is True:
                m['successes'] += 1
                if inst['end_step'] is not None and inst['start_step'] is not None:
                    dt = max(0, int(inst['end_step']) - int(inst['start_step']))
                    # average over successes
                    m['avg_t'] = dt if m['avg_t'] is None else (m['avg_t']*(m['successes']-1)+dt)/m['successes']
                    m['min_t'] = dt if m['min_t'] is None else min(m['min_t'], dt)
                    m['max_t'] = dt if m['max_t'] is None else max(m['max_t'], dt)
            comms = inst.get('comms') or 'unknown'
            m['comms'][comms] = m['comms'].get(comms, 0) + 1
            per_tb[(inst['task'], b)].append((k, inst['success'] is True))

        for v in agg.values():
            v['cr'] = (v['successes'] / v['attempts']) if v['attempts'] else None

        # compute k* (smallest k within 95% of best CR)
        kstar = {}
        from collections import defaultdict
        for (task, b), rows in per_tb.items():
            per_k = defaultdict(lambda: [0,0])
            for k, succ in rows:
                per_k[k][0] += 1
                per_k[k][1] += int(succ)
            crs = {k: (succ/att) if att else 0.0 for k,(att,succ) in per_k.items()}
            if not crs:
                continue
            max_cr = max(crs.values())
            thr = 0.95 * max_cr
            ks = sorted([k for k,cr in crs.items() if cr >= thr])
            if ks:
                kstar[f"{task}|bucket={b}"] = int(ks[0])

        return dict(agg), kstar

    def _build_tcg(self, instances, bucket: int):
        """Template-Context Graph.
        Keys: "task|bucket|k|comms|template" -> metrics
        """
        from collections import defaultdict
        def key(task,b,k,comms,tpl): return f"{task}|bucket={b}|k={k}|comms={comms}|template={tpl}"
        agg = defaultdict(lambda: {'attempts':0,'successes':0,'avg_t':None})
        for inst in instances:
            b = self._bucketize(inst['start_step'], bucket)
            k = inst['k']
            comms = inst.get('comms') or 'unknown'
            kkey = key(inst['task'], b, k, comms, inst['template'])
            a = agg[kkey]
            a['attempts'] += 1
            if inst['success'] is True:
                a['successes'] += 1
                if inst['end_step'] is not None and inst['start_step'] is not None:
                    dt = max(0, int(inst['end_step']) - int(inst['start_step']))
                    a['avg_t'] = dt if a['avg_t'] is None else (a['avg_t']*(a['successes']-1)+dt)/a['successes']
        for v in agg.values():
            v['cr'] = (v['successes']/v['attempts']) if v['attempts'] else None
        return dict(agg)

    def _build_pdg(self, tcg_view):
        """Plan-Delta Graph built from TCG: compare templates within the SAME context.
        For each context (task,bucket,k,comms), compute pairwise deltas A->B with cr_gain>0.
        Keys: "templateA -> templateB" -> list of contexts where it helped.
        """
        from collections import defaultdict

        # Group by context
        by_ctx = defaultdict(dict)  # ctx_key -> {template: cr}
        for k, v in tcg_view.items():
            # parse key back to parts
            parts = {}
            for seg in k.split('|'):
                if '=' in seg:
                    a,b = seg.split('=',1)
                    parts[a]=b
                else:
                    parts.setdefault('task', seg)
            task = parts.get('task')
            bucket = parts.get('bucket')
            ksize = parts.get('k')
            comms = parts.get('comms')
            template = parts.get('template')
            ctx = f"{task}|bucket={bucket}|k={ksize}|comms={comms}"
            by_ctx[ctx][template] = v.get('cr', 0.0)

        def delta_str(a, b):
            def toks(s): return [t.strip() for t in s.split('->')]
            A, B = toks(a), toks(b)
            if len(B) == len(A)+1 and all(x==y for x,y in zip(A, B[:len(A)])):
                return f"Insert({B[-1]})"
            if len(A) == len(B)+1 and all(x==y for x,y in zip(B, A[:len(B)])):
                return f"Delete({A[-1]})"
            for x,y in zip(A,B):
                if x!=y: return f"Replace({x}->{y})"
            return "Edit"

        pdg = defaultdict(list)
        for ctx, templ2cr in by_ctx.items():
            if len(templ2cr) < 2:
                continue
            items = list(templ2cr.items())
            for i in range(len(items)):
                for j in range(len(items)):
                    if i==j: continue
                    A, crA = items[i]
                    B, crB = items[j]
                    gain = (crB - crA)
                    if gain > 0:
                        pdg[f"{A} -> {B}"].append({'delta': delta_str(A,B), 'cr_gain': round(gain,4), 'where': ctx})
        return dict(pdg)


    def _episode_instance_intervals(self, rec: 'EpisodeRecord', episode_id: str):
        """Return list of (prefixed_node_id, start, end, agent_id) for instance (leaf) nodes within an episode.
        Uses only rec.wm.task_data structure to reconstruct node ids.
        """
        spans = []
        ep_max = (rec.wm.episode_data or {}).get('max_timestep', None)
        tdata = rec.wm.task_data or {}
        # Maintain template index consistent with graph building
        for task_idx, (task_name, task_info) in enumerate(tdata.items()):
            templates = (task_info or {}).get('templates', {})
            for template_idx, (template_name, template_info) in enumerate(templates.items()):
                template_id = f"{task_name}_template_{template_idx}"
                for inst_idx, inst in enumerate(template_info.get('instances', [])):
                    instance_id = f"{template_id}_instance_{inst_idx}"
                    node_id = f"{episode_id}:{instance_id}"
                    start = inst.get('start_step')
                    end = inst.get('end_step', None)
                    if end is None:
                        end = ep_max if ep_max is not None else start
                    agent = inst.get('agent_id', 'unknown')
                    if start is not None:
                        spans.append((node_id, int(start), int(end), str(agent)))
        return spans

    @staticmethod
    def _overlap(a_start, a_end, b_start, b_end):
        return (a_start is not None and b_start is not None) and (a_start <= b_end and b_start <= a_end)

    def _compute_overlap_edges(self):
        """Compute dotted-line edges between instance nodes with overlapping time within each episode."""
        edges = set()
        for episode_id, rec in self.episodes.items():
            spans = self._episode_instance_intervals(rec, episode_id)
            # Compare all pairs within the episode
            for i in range(len(spans)):
                n1, s1, e1, _a1 = spans[i]
                if n1 not in self.node_positions:  # ensure exists in current graph
                    continue
                for j in range(i+1, len(spans)):
                    n2, s2, e2, _a2 = spans[j]
                    if n2 not in self.node_positions:
                        continue
                    if self._overlap(s1, e1, s2, e2):
                        edges.add(tuple(sorted((n1, n2))))
        return list(edges)

    # ------------------------------
    # Internals
    # ------------------------------
    def _universe_node_id(self) -> str:
        return f"{self.name}_ROOT"

    def _recompute_aggregates(self):
        s = MultiverseStats()
        s.num_episodes = len(self.episodes)

        episode_times = []
        for rec in self.episodes.values():
            ep = rec.wm.episode_data
            if ep.get('completed'):
                s.episodes_completed += 1
            if ep.get('max_timestep') is not None:
                episode_times.append(ep['max_timestep'])
            for tname, tinfo in rec.wm.task_data.items():
                ts = s.task_stats.setdefault(tname, {'seen': 0, 'completes': 0, 'times': []})
                ts['seen'] += 1
                if tinfo.get('final_success'):
                    ts['completes'] += 1
                    if tinfo.get('completion_time') is not None:
                        ts['times'].append(tinfo['completion_time'])

        if episode_times:
            s.episode_min_time = int(min(episode_times))
            s.episode_max_time = int(max(episode_times))
            s.episode_avg_time = float(sum(episode_times) / len(episode_times))

        for tname, ts in s.task_stats.items():
            times = ts['times']
            ts['completion_rate'] = (ts['completes'] / ts['seen']) if ts['seen'] else None
            ts['min_time'] = int(min(times)) if times else None
            ts['max_time'] = int(max(times)) if times else None
            ts['avg_time'] = (sum(times) / len(times)) if times else None

        self.stats = s

    def _stats_dict(self) -> Dict:
        s = self.stats
        return {
            'num_episodes': s.num_episodes,
            'episodes_completed': s.episodes_completed,
            'episode_completion_rate': (s.episodes_completed / s.num_episodes) if s.num_episodes else None,
            'episode_min_time': s.episode_min_time,
            'episode_max_time': s.episode_max_time,
            'episode_avg_time': s.episode_avg_time,
            'task_stats': s.task_stats,
        }

    def _build_universe_graph(self):
        G = nx.Graph()

        colors = {
            'universe': '#34495e',
            'episode_complete': '#8e44ad',
            'episode_incomplete': '#e67e22',
            'task_success': '#2ecc71',
            'task_failed': '#e74c3c',
            'template_success': '#27ae60',
            'template_failed': '#c0392b',
            'instance_success': '#1e8449',
            'instance_failed': '#922b21',
            'instance_ongoing': '#5d6d7e'
        }

        U = self._universe_node_id()
        G.add_node(U, node_type='universe')
        self.node_positions = {U: (0.0, 0.0)}
        self.node_labels = {}

        # Universe label with aggregated stats
        s = self._stats_dict()
        task_lines = []
        for tname, ts in sorted(s['task_stats'].items()):
            cr = f"{ts['completion_rate']*100:.1f}%" if ts.get('completion_rate') is not None else "—"
            avgt = f"{ts['avg_time']:.1f}" if ts.get('avg_time') is not None else "—"
            mint = ts.get('min_time', '—'); maxt = ts.get('max_time', '—')
            task_lines.append(f"{tname}: CR {cr}, T(avg/min/max) {avgt}/{mint}/{maxt}")
        if len(task_lines) > 12:
            task_lines = task_lines[:12] + [f"... (+{len(task_lines)-12} more tasks)"]

        ecr = s['episode_completion_rate']
        ecr_str = f"{ecr*100:.1f}%" if ecr is not None else "—"
        avg_str = f"{s['episode_avg_time']:.1f}" if s['episode_avg_time'] is not None else '—'
        min_str = str(s['episode_min_time']) if s['episode_min_time'] is not None else '—'
        max_str = str(s['episode_max_time']) if s['episode_max_time'] is not None else '—'

        uni_label = (
            f"UNIVERSE: {self.name}\n"
            f"Episodes: {s['episodes_completed']}/{s['num_episodes']} completed ({ecr_str})\n"
            f"Episode time (avg/min/max): {avg_str}/{min_str}/{max_str}\n"
            f"Task aggregates:\n" + ("\n".join(task_lines) if task_lines else "—")
        )
        self.node_labels[U] = uni_label
        self.node_colors = [colors['universe']]
        self.node_sizes = [8000]

        # Episode anchors around a circle
        n_ep = len(self.episodes)
        radius = 18.0
        if n_ep == 1:
            anchors = [(0.0, 14.0)]
        else:
            anchors = [
                (radius * math.cos(2*math.pi*i / n_ep),
                 radius * math.sin(2*math.pi*i / n_ep))
                for i in range(n_ep)
            ]

        for (episode_id, rec), anchor in zip(self.episodes.items(), anchors):
            rec.anchor_pos = anchor
            wm = rec.wm

            ep_node_src = "EPISODE_STATUS"
            ep_node = f"{episode_id}:{ep_node_src}"
            G.add_node(ep_node, node_type='episode')
            G.add_edge(U, ep_node)
            self.node_positions[ep_node] = anchor

            ep = wm.episode_data
            status = "COMPLETED" if ep.get('completed') else "INCOMPLETE"
            comp_str = ", ".join([f"{o}.{t}@T{ts}" for t, ts, o in ep.get('completed_blocks_order', [])]) or "None"
            inc_str = ", ".join(ep.get('incomplete_blocks', [])) or "None"
            ep_label = (f"{episode_id} — EPISODE {status}\n"
                        f"Timestep: {ep.get('max_timestep', 0)}\n"
                        f"Total Blocks: {ep.get('total_blocks', 0)}\n"
                        f"Completed ({ep.get('completed_blocks', 0)}): {comp_str}\n"
                        f"Incomplete ({ep.get('remaining_blocks', 0)}): {inc_str}")
            self.node_labels[ep_node] = ep_label
            self.node_colors.append(colors['episode_complete' if ep.get('completed') else 'episode_incomplete'])
            self.node_sizes.append(5000)

            # copy WM nodes
            for n, attrs in wm.graph.nodes(data=True):
                if n == ep_node_src: continue
                prefixed = f"{episode_id}:{n}"
                G.add_node(prefixed, **attrs)
            for u, v in wm.graph.edges():
                if ep_node_src in (u, v):
                    other = v if u == ep_node_src else u
                    G.add_edge(ep_node, f"{episode_id}:{other}")
                else:
                    G.add_edge(f"{episode_id}:{u}", f"{episode_id}:{v}")
            ax, ay = anchor
            for n in wm.graph.nodes():
                if n == ep_node_src: continue
                pn = f"{episode_id}:{n}"
                x, y = wm.node_positions[n]
                self.node_positions[pn] = (x + ax, y + ay)
                self.node_labels[pn] = wm.node_labels[n]
                typ = wm.graph.nodes[n].get('node_type')
                if typ == 'task':
                    self.node_colors.append(colors['task_success' if 'COMPLETED' in wm.node_labels[n] else 'task_failed'])
                    self.node_sizes.append(3000)
                elif typ == 'template':
                    self.node_colors.append(colors['template_success'])
                    self.node_sizes.append(2000)
                elif typ == 'instance':
                    lbl = wm.node_labels[n]
                    if "Status: SUCCESS" in lbl:
                        self.node_colors.append(colors['instance_success'])
                    elif "Status: FAILED" in lbl:
                        self.node_colors.append(colors['instance_failed'])
                    else:
                        self.node_colors.append(colors['instance_ongoing'])
                    self.node_sizes.append(1100)
                else:
                    self.node_colors.append('#95a5a6')
                    self.node_sizes.append(1000)

        self.universe_graph = G
