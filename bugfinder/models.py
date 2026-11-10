from dataclasses import asdict, dataclass

@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    confidence: str
    message: str
    recommendation: str
    file_path: str
    line: int
    column: int = 1

    def to_dict(self):
        return asdict(self)
