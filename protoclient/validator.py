from protocoin.datatypes import values
from protocoin import util

from db.models import Block

max_target = util.bits_to_target(values.HIGHEST_TARGET_BITS)
target_timespan = 60 * 60 * 24 * 7 * 2 # We want 2016 blocks to take 2 weeks.
retarget_interval = 2016 # Blocks

def validate_block(block_message, prev_block):
    """Validate a new block"""
    # Calculate the current target
    target = get_target(block_message, prev_block)

    if block_message.prev_hash() != prev_block.calculate_hash():
        # TODO: Proper logging
        print("Rejecting block %s: The previous block hash (%s) differs from our latest block hash (%s)" %
            (block_message, block_message.prev_hash(), prev_block.calculate_hash()))
        return False

    if not block_message.validate_proof_of_work(target):
        # TODO proper logging
        print("Block #%s invalid: (%s)" % (prev_block.height + 1, target))
        return False

    return True

def get_target(block_message, prev_block):
    from testnet import testnet

    current_height = prev_block.height + 1
    target = util.bits_to_target(prev_block.bits)

    # If testnet, don't use 20-minute-rule targets; iterate backwards to last proper target
    if testnet:
        height = current_height - 1
        while height > 0 and height % retarget_interval != 0:
            height -= 1
        target = util.bits_to_target(Block.objects.get(height=height).bits)

    if current_height % retarget_interval == 0:
        target = retarget(target, prev_block)

    # 20 minute rule for testnet
    if testnet:
        if current_height % retarget_interval != 0 and block_message.timestamp - prev_block.timestamp_unixtime() > 1200:
            target = max_target

    return target

def retarget(target, prev_block):
    """
    Every *retarget_interval* blocks, recalculate the target based on the wanted timespan.
    For all other blocks, the target remains equal to the previous target.
    """
    current_height = prev_block.height + 1
    retarget_height = 0 if current_height < retarget_interval else current_height - retarget_interval
    last_retargeted_block = Block.objects.get(height=retarget_height)

    timespan = prev_block.timestamp_unixtime() - last_retargeted_block.timestamp_unixtime()

    # Limit adjustment step
    if timespan > target_timespan * 4:
        timespan = target_timespan * 4
    elif timespan < target_timespan / 4:
        timespan = target_timespan / 4

    # Adjust the target
    target *= timespan
    target /= target_timespan

    # Round the target with the packed representation
    target = util.bits_to_target(util.target_to_bits(target))

    # Never exceed the maximum target
    if target > max_target:
        target = max_target

    return target
