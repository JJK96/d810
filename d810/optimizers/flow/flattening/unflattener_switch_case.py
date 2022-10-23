import logging
from ida_hexrays import *

from d810.hexrays_helpers import append_mop_if_not_in_list
from d810.optimizers.flow.flattening.generic import GenericDispatcherBlockInfo, GenericDispatcherInfo, \
    GenericDispatcherCollector, GenericDispatcherUnflatteningRule


unflat_logger = logging.getLogger('D810.unflat')
FLATTENING_JUMP_OPCODES = [m_jtbl]


class TigressSwitchDispatcherBlockInfo(GenericDispatcherBlockInfo):
    pass


class TigressSwitchDispatcherInfo(GenericDispatcherInfo):
    def explore(self, blk: mblock_t):
        self.reset()
        if not self._is_candidate_for_dispatcher_entry_block(blk):
            return False
        self.mop_compared, mcases = self._get_comparison_info(blk)
        self.entry_block = TigressSwitchDispatcherBlockInfo(blk)
        self.entry_block.parse()
        for used_mop in self.entry_block.use_list:
            append_mop_if_not_in_list(used_mop, self.entry_block.assume_def_list)
        self.dispatcher_internal_blocks.append(self.entry_block)
        for possible_values, target_block_serial in zip(mcases.c.values, mcases.c.targets):
            if target_block_serial == self.entry_block.blk.serial:
                continue
            exit_block = TigressSwitchDispatcherBlockInfo(blk.mba.get_mblock(target_block_serial), self.entry_block)
            self.dispatcher_exit_blocks.append(exit_block)
            if len(possible_values) == 0:
                continue
            self.comparison_values.append(possible_values[0])
        return True

    def _get_comparison_info(self, blk: mblock_t):
        # blk.tail must be a jtbl
        if (blk.tail is None) or (blk.tail.opcode != m_jtbl):
            return None, None
        return blk.tail.l, blk.tail.r

    def _is_candidate_for_dispatcher_entry_block(self, blk: mblock_t):
        if (blk.tail is None) or (blk.tail.opcode != m_jtbl):
            return False
        return True


class TigressSwitchDispatcherCollector(GenericDispatcherCollector):
    DISPATCHER_CLASS = TigressSwitchDispatcherInfo
    DEFAULT_DISPATCHER_MIN_INTERNAL_BLOCK = 0
    DEFAULT_DISPATCHER_MIN_EXIT_BLOCK = 2
    DEFAULT_DISPATCHER_MIN_COMPARISON_VALUE = 2


class UnflattenerSwitchCase(GenericDispatcherUnflatteningRule):
    DESCRIPTION = "Remove control flow flattening generated by Tigress with Switch case dispatcher"
    DISPATCHER_COLLECTOR_CLASS = TigressSwitchDispatcherCollector
    DEFAULT_UNFLATTENING_MATURITIES = [MMAT_GLBOPT1,MMAT_GLBOPT2]
    DEFAULT_MAX_DUPLICATION_PASSES = 20
    DEFAULT_MAX_PASSES = 7
