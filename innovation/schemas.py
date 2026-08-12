from typing import List

try:
    from pydantic import BaseModel, Field, ValidationError
    has_pydantic = True
except ImportError:
    has_pydantic = False

    class _FallbackBaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            d = {}
            for k, v in self.__dict__.items():
                if hasattr(v, "dict"):
                    d[k] = v.dict()
                else:
                    d[k] = v
            return d

    BaseModel = _FallbackBaseModel

    def Field(*args, **kwargs):
        return None

    class ValidationError(Exception):
        pass

if has_pydantic:
    class ScoresSchema(BaseModel):
        design_integrity: float = Field(
            ..., 
            description="Structural organization score, indicating decoupling and clean boundaries.", 
            ge=0.0, 
            le=1.0
        )
        structural_novelty: float = Field(
            ..., 
            description="Code structural originality score, indicating customization and absence of boilerplate.", 
            ge=0.0, 
            le=1.0
        )
        readme_consistency: float = Field(
            ..., 
            description="Documentation consistency score, mapping mentioned modules against actual code directories.", 
            ge=0.0, 
            le=1.0
        )

    class ArchitectureEvaluationSchema(BaseModel):
        detected_patterns: List[str] = Field(
            ..., 
            description="Design patterns detected in the workspace layout (e.g. MVC, Monolith, Pipeline)."
        )
        manifest_mismatches: List[str] = Field(
            ..., 
            description="Listing discrepancies between import structures and package manifests."
        )
        readme_authenticity: str = Field(
            ..., 
            description="Detailed analysis of whether the README describes the actual code structure accurately."
        )
        scores: ScoresSchema = Field(
            ..., 
            description="Consolidated score breakdown metrics."
        )
        critique_summary: str = Field(
            ..., 
            description="Full systems architecture critique and design feedback."
        )
else:
    class ScoresSchema(BaseModel):
        pass
    class ArchitectureEvaluationSchema(BaseModel):
        pass
