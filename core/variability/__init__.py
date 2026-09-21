"""
Variability engine: semantic variation of wildcard prompts.

Moves each random pick to a semantic neighbour inside its own list (small drift on most slots,
a larger jump on a few), and can steer away from recently generated prompts. Needs numpy; the
embedding model is pluggable (see embedders.py). No ComfyUI dependency in this package.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from .embedders import (
    ComfyClipEmbedder,
    Embedder,
    LexicalEmbedder,
    OpenClipEmbedder,
    Qwen3VLEmbedder,
    SentenceTransformerEmbedder,
    clip_label,
)
from .directions import NONE as NO_DIRECTION, DirectionAxis, load_directions
from .memory import RepulsionMemory
from .moves import (
    direction, direction_pick, farthest_point_select, leaning_pick, max_similarity, neighbour_pick, ranked_neighbours,
)
from .survival import ConceptScore, score_concepts, text_windows
from .variation import SemanticVariator, SlotMove, VariationResult, VariationSettings
from .vector_cache import VectorCache

__all__ = [
    "Embedder", "LexicalEmbedder", "SentenceTransformerEmbedder", "OpenClipEmbedder", "Qwen3VLEmbedder",
    "ComfyClipEmbedder", "clip_label", "RepulsionMemory", "VectorCache",
    "neighbour_pick", "ranked_neighbours", "farthest_point_select", "max_similarity", "direction", "direction_pick",
    "leaning_pick", "DirectionAxis", "load_directions", "NO_DIRECTION",
    "ConceptScore", "score_concepts", "text_windows",
    "SemanticVariator", "SlotMove", "VariationResult", "VariationSettings",
]
