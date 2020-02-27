import enum


class KenanteChatMessageType(enum.Enum):
    ServerNotify = "ServerNotify"
    Text = "Text"
    Media = "Media"
    Leave = "Leave"
    History = "History"
