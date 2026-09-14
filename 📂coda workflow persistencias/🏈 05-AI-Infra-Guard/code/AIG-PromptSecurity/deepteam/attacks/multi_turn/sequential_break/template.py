"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'c66a47a2871f2b02367dc184668fa2f69ab83058f804e2482683c4f6ab28e09a'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class SequentialBreakTemplate:
    def rewrite_dialogue_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.rewrite_dialogue_prompt', kwargs)
    def rewrite_question_bank_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.rewrite_question_bank_prompt', kwargs)
    def get_dialogue_template(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.get_dialogue_template', kwargs)
    def get_question_bank_template(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.get_question_bank_template', kwargs)
    def dialogue_judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.dialogue_judge', kwargs)
    def non_refusal(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.non_refusal', kwargs)
    def question_bank_judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.question_bank_judge', kwargs)
    def _prisoner_template(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate._prisoner_template', kwargs)
    def _student_template(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate._student_template', kwargs)
    def _researcher_template(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate._researcher_template', kwargs)
    def _generic_template(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate._generic_template', kwargs)
    def rewrite_game_environment_prompt(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.rewrite_game_environment_prompt', kwargs)
    def get_game_environment_template(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.get_game_environment_template', kwargs)
    def game_environment_judge(self, *args, **kwargs):
        return _yaiwes_checkpoint('SequentialBreakTemplate.game_environment_judge', kwargs)
