"""Cloud film image viewer API and pages."""
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent.parent / "templates"))

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
CLOUD_FILM_DIR = _PROJECT_ROOT / "data" / "medical_images"


@router.get("/cloud-films", response_class=HTMLResponse)
async def list_cloud_films(request: Request):
    """List all cloud film datasets."""
    films = []
    if CLOUD_FILM_DIR.exists():
        for study_dir in sorted(CLOUD_FILM_DIR.iterdir()):
            if not study_dir.is_dir():
                continue
            
            # Read manifest for series info
            manifest_path = study_dir / "manifest.json"
            manifest = None
            if manifest_path.exists():
                import json
                try:
                    manifest = json.loads(manifest_path.read_text())
                except:
                    pass
            
            # Count total images across all series dirs
            total_images = 0
            series_dirs = []
            for d in sorted(study_dir.iterdir()):
                if d.is_dir() and d.name.startswith("series_"):
                    imgs = list(d.glob("*.jpg")) + list(d.glob("*.png"))
                    total_images += len(imgs)
                    series_dirs.append(d.name)
            
            # Also check legacy jpeg dir
            jpeg_dir = study_dir / "jpeg"
            if jpeg_dir.exists():
                jpeg_count = len(list(jpeg_dir.glob("*.jpg")))
                total_images += jpeg_count
            
            films.append({
                "id": study_dir.name,
                "name": manifest.get("patient", study_dir.name.replace("_", " ").title()) if manifest else study_dir.name.replace("_", " ").title(),
                "study_date": manifest.get("study_date", "") if manifest else "",
                "patient_id": manifest.get("patient_id", "") if manifest else "",
                "total_images": total_images,
                "series_count": len(series_dirs),
                "has_manifest": manifest is not None,
            })
    
    return templates.TemplateResponse(request, "cloud_film/list.html", {"films": films})


@router.get("/cloud-films/{study_id}", response_class=HTMLResponse)
async def view_cloud_film(request: Request, study_id: str):
    """View a specific cloud film study organized by series."""
    study_dir = CLOUD_FILM_DIR / study_id
    if not study_dir.exists():
        return HTMLResponse("<h1>Study not found</h1>", status_code=404)
    
    import json
    
    # Read manifest
    manifest_path = study_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except:
            pass
    
    # Organize images by series
    series_data = []
    for d in sorted(study_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("series_"):
            continue
        
        # Parse series number from dir name: "series_04_SEGMENT_..."
        parts = d.name.split("_", 2)
        snum = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        
        imgs = sorted([f.name for f in d.glob("*.jpg")] + [f.name for f in d.glob("*.png")])
        if not imgs:
            continue
        
        # Get metadata from manifest
        meta = manifest.get("series", {}).get(str(snum), {})
        
        series_data.append({
            "num": snum,
            "name": meta.get("name", d.name),
            "protocol": meta.get("protocol", ""),
            "modality": meta.get("modality", ""),
            "dir": d.name,
            "images": imgs,
            "count": len(imgs),
            "expected": meta.get("expected", 0),
        })
    
    return templates.TemplateResponse(request, "cloud_film/viewer.html", {
        "study_id": study_id,
        "patient_name": manifest.get("patient", ""),
        "patient_id": manifest.get("patient_id", ""),
        "study_date": manifest.get("study_date", ""),
        "series_data": series_data,
        "total_images": sum(s["count"] for s in series_data),
    })
