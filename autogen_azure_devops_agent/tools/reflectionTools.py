from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json

@dataclass
class CodeReview:
    """
    Representa una revisión de código con comentarios específicos.
    """
    code: str
    reviewer_name: str
    issues: List[Dict[str, Any]]
    approved: bool
    suggestions: List[Dict[str, Any]]
    reasoning: str

@dataclass
class CodeImplementation:
    """
    Representa una implementación de código realizada por un agente.
    """
    code: str
    implementor_name: str
    description: str
    file_path: str
    purpose: str

def create_code_implementation(
    code: str,
    implementor_name: str,
    description: str,
    file_path: str,
    purpose: str
) -> Dict[str, Any]:
    """
    Crea un registro de implementación de código para ser revisado.
    
    Args:
        code: El código implementado
        implementor_name: Nombre del agente implementador
        description: Descripción de la implementación
        file_path: Ruta del archivo donde se implementará
        purpose: Propósito de la implementación
        
    Returns:
        Un diccionario con los datos de la implementación
    """
    implementation = CodeImplementation(
        code=code,
        implementor_name=implementor_name,
        description=description,
        file_path=file_path,
        purpose=purpose
    )
    
    return {
        "code": implementation.code,
        "implementor_name": implementation.implementor_name,
        "description": implementation.description,
        "file_path": implementation.file_path,
        "purpose": implementation.purpose,
        "status": "pending_review"
    }

def create_code_review(
    code: str,
    reviewer_name: str,
    issues: List[Dict[str, Any]],
    approved: bool,
    suggestions: List[Dict[str, Any]],
    reasoning: str
) -> Dict[str, Any]:
    """
    Crea una revisión de código para una implementación.
    
    Args:
        code: El código revisado (puede incluir cambios sugeridos)
        reviewer_name: Nombre del agente revisor
        issues: Lista de problemas encontrados en el código
        approved: Si el código está aprobado o no
        suggestions: Lista de sugerencias para mejorar el código
        reasoning: Explicación detallada de la revisión
        
    Returns:
        Un diccionario con los datos de la revisión
    """
    review = CodeReview(
        code=code,
        reviewer_name=reviewer_name,
        issues=issues,
        approved=approved,
        suggestions=suggestions,
        reasoning=reasoning
    )
    
    return {
        "code": review.code,
        "reviewer_name": review.reviewer_name,
        "issues": review.issues,
        "approved": review.approved,
        "suggestions": review.suggestions,
        "reasoning": review.reasoning,
        "status": "reviewed"
    }

def create_architectural_review(
    implementation: Dict[str, Any],
    code_follows_patterns: bool,
    identified_patterns: List[str],
    solid_principles_violations: List[Dict[str, str]],
    architectural_feedback: str,
    approved: bool,
    suggested_improvements: List[str]
) -> Dict[str, Any]:
    """
    Crea una revisión arquitectónica de código.
    
    Args:
        implementation: La implementación a revisar
        code_follows_patterns: Si el código sigue los patrones establecidos
        identified_patterns: Patrones identificados en el código
        solid_principles_violations: Violaciones de principios SOLID
        architectural_feedback: Feedback arquitectónico detallado
        approved: Si la arquitectura está aprobada o no
        suggested_improvements: Mejoras arquitectónicas sugeridas
        
    Returns:
        Un diccionario con los datos de la revisión arquitectónica
    """
    return {
        "original_implementation": implementation,
        "code_follows_patterns": code_follows_patterns,
        "identified_patterns": identified_patterns,
        "solid_principles_violations": solid_principles_violations,
        "architectural_feedback": architectural_feedback,
        "approved": approved,
        "suggested_improvements": suggested_improvements,
        "status": "architecturally_reviewed"
    }

def create_quality_review(
    implementation: Dict[str, Any],
    testability_score: int,
    edge_cases_handled: bool,
    error_handling_adequate: bool,
    performance_concerns: List[str],
    security_issues: List[Dict[str, str]],
    code_quality_feedback: str,
    approved: bool,
    test_suggestions: List[str]
) -> Dict[str, Any]:
    """
    Crea una revisión de calidad de código.
    
    Args:
        implementation: La implementación a revisar
        testability_score: Puntuación de testabilidad (1-10)
        edge_cases_handled: Si se manejan casos límite
        error_handling_adequate: Si el manejo de errores es adecuado
        performance_concerns: Preocupaciones de rendimiento
        security_issues: Problemas de seguridad encontrados
        code_quality_feedback: Feedback detallado de calidad
        approved: Si la calidad está aprobada o no
        test_suggestions: Sugerencias de pruebas
        
    Returns:
        Un diccionario con los datos de la revisión de calidad
    """
    return {
        "original_implementation": implementation,
        "testability_score": testability_score,
        "edge_cases_handled": edge_cases_handled,
        "error_handling_adequate": error_handling_adequate,
        "performance_concerns": performance_concerns,
        "security_issues": security_issues,
        "code_quality_feedback": code_quality_feedback,
        "approved": approved,
        "test_suggestions": test_suggestions,
        "status": "quality_reviewed"
    }

def get_review_summary(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Genera un resumen de múltiples revisiones.
    
    Args:
        reviews: Lista de revisiones a resumir
        
    Returns:
        Un diccionario con el resumen de las revisiones
    """
    architect_reviews = [r for r in reviews if r.get("status") == "architecturally_reviewed"]
    quality_reviews = [r for r in reviews if r.get("status") == "quality_reviewed"]
    general_reviews = [r for r in reviews if r.get("status") == "reviewed"]
    
    all_approved = all(r.get("approved", False) for r in reviews)
    
    issues = []
    for review in reviews:
        if "issues" in review:
            issues.extend(review["issues"])
        if "solid_principles_violations" in review:
            issues.extend([{"type": "SOLID Violation", "description": v["description"]} 
                         for v in review.get("solid_principles_violations", [])])
        if "security_issues" in review:
            issues.extend([{"type": "Security Issue", "description": s["description"]} 
                         for s in review.get("security_issues", [])])
    
    suggestions = []
    for review in reviews:
        if "suggestions" in review:
            suggestions.extend(review["suggestions"])
        if "suggested_improvements" in review:
            suggestions.extend([{"type": "Architectural Improvement", "description": s} 
                              for s in review.get("suggested_improvements", [])])
        if "test_suggestions" in review:
            suggestions.extend([{"type": "Test Suggestion", "description": s} 
                              for s in review.get("test_suggestions", [])])
    
    return {
        "total_reviews": len(reviews),
        "architectural_reviews": len(architect_reviews),
        "quality_reviews": len(quality_reviews),
        "general_reviews": len(general_reviews),
        "all_approved": all_approved,
        "issues": issues,
        "suggestions": suggestions,
        "needs_changes": not all_approved or len(issues) > 0
    }

def reflection_cycle_needed(review_summary: Dict[str, Any]) -> bool:
    """
    Determina si se necesita un ciclo de reflexión adicional basado en un resumen de revisión.
    
    Args:
        review_summary: El resumen de revisiones a analizar
        
    Returns:
        True si se necesita un ciclo adicional de reflexión, False en caso contrario
    """
    # Si no todas las revisiones están aprobadas, se necesita un ciclo adicional
    if not review_summary.get("all_approved", False):
        return True
    
    # Si hay problemas críticos, se necesita un ciclo adicional
    if len(review_summary.get("issues", [])) > 0:
        # Verificar si hay algún problema crítico
        for issue in review_summary.get("issues", []):
            if issue.get("type") in ["SOLID Violation", "Security Issue"]:
                return True
    
    # Si se detecta explícitamente que necesita cambios
    if review_summary.get("needs_changes", False):
        return True
    
    # Por defecto, no se necesita un ciclo adicional
    return False