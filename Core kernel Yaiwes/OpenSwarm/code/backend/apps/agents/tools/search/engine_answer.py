"""What a keyless search engine actually said: results, an honest nothing, or a refusal.

"Closed" and "genuinely no hits" look identical on the wire (both are a 200
with no result anchors) and the caller has to act on them differently: a
refusal is a failed tier that should count against the engine's breaker, an
empty result set is the honest answer to a nonsense query."""

from pydantic import BaseModel, ConfigDict


class EngineAnswer(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    results: str = ""
    # Challenge, HTTP error, or markup we no longer recognise: the engine did not answer the question.
    refused: bool = False
