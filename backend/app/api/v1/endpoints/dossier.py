import os
from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from app.schemas.dossier import DossierRequestSchema
from app.services.pdf_generator import DossierService

router = APIRouter()


@router.post(
    "/generate",
    status_code=status.HTTP_200_OK,
    summary="Generate PDF Evidence Dossier Report",
    description=(
        "Generates a forensic threat intelligence PDF report document using ReportLab "
        "and streams it to the client as a downloadable attachment."
    ),
    response_class=FileResponse,
)
async def generate_dossier_pdf(payload: DossierRequestSchema) -> FileResponse:
    """Generates PDF evidence dossier and returns a FileResponse attachment."""
    file_path = await DossierService.generate_pdf_report(
        target_handle=payload.target_handle,
        findings=payload.findings,
    )

    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
    )
