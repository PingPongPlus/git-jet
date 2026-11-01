"""Only these limits permit retrying a render at lower quality."""


class FrameLimitError(ValueError):
    pass


class GifSizeLimitError(ValueError):
    pass
