def split(text: str, block_length: int = 500):
    text = text.strip()
    split_blocks = []
    length = len(text)

    cursor = 0
    while cursor < length:
        block = text[cursor:cursor + block_length]
        split_blocks.append(block)
        cursor = cursor + block_length
    return split_blocks
