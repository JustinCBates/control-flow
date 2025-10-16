"""
Structure Operations Library

Universal operations for manipulating hierarchical structures.
Supports insert, delete, move, renumber, swap, and reorder operations
on any hierarchical data (dictionaries, lists, YAML, JSON).

No domain coupling - works with any hierarchical structure.
"""

from .mover import StructureMover, MoveOperation, MoveResult
from .swapper import StructureSwapper, SwapOperation, SwapResult
# from .reorderer import StructureReorderer, ReorderOperation, ReorderResult  # TODO: Implement

__all__ = [
    'StructureMover',
    'MoveOperation',
    'MoveResult',
    'StructureSwapper',
    'SwapOperation',
    'SwapResult',
    # 'StructureReorderer',
    # 'ReorderOperation',
    # 'ReorderResult',
]
