def clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines]

    result_lines = []
    previous_was_blank = False

    for line in cleaned_lines:
        is_blank = (line == "")

        if is_blank and previous_was_blank:
            continue  # skip this line entirely — we already have a blank line in result_lines

        result_lines.append(line)
        previous_was_blank = is_blank

    return "\n".join(result_lines)