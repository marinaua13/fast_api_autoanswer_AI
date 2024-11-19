from better_profanity import profanity


def check_profanity(content: str) -> bool:
    return profanity.contains_profanity(content)


def censor_content(content: str) -> str:
    return profanity.censor(content)
