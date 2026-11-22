from typing import List


def split_message(text: str, max_length: int = 3900) -> List[str]:
    """
    Splits long output into Telegram-safe message chunks (~3900 characters each).
    Attempts to split by line boundaries to keep logs readable.
    """
    if not text:
        return ["(No output)"]

    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []
    lines = text.splitlines(keepends=True)
    current_chunk: List[str] = []
    current_len = 0

    for line in lines:
        if len(line) > max_length:
            # Handle extremely long single lines without breaks
            if current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_len = 0
            for i in range(0, len(line), max_length):
                chunks.append(line[i : i + max_length])
            continue

        if current_len + len(line) > max_length:
            chunks.append("".join(current_chunk))
            current_chunk = [line]
            current_len = len(line)
        else:
            current_chunk.append(line)
            current_len += len(line)

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


def format_code_block(content: str, language: str = "") -> str:
    """Wraps text content inside a markdown code block."""
    clean_content = content.replace("```", "'''")
    return f"```{language}\n{clean_content}\n```"
