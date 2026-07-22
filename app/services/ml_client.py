"""
Backend ML Client — bridge to Vision, Scam-Intelligence, and Intelligence Engine microservices.

Ports (from settings):
  - SCAM_INTELLIGENCE_URL: http://localhost:8001 → /text, /audio, /url, /risk
  - VISION_URL:            http://localhost:8002 → /currency, /document, /ocr, /qr, /image
  - INTELLIGENCE_URL:      http://localhost:8003 → /fuse, /graph/query, /evidence/generate
"""
import asyncio
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.logging import logger


class MLClient:
    def __init__(self):
        self.scam = httpx.AsyncClient(base_url=settings.SCAM_INTELLIGENCE_URL, timeout=60.0)
        self.vision = httpx.AsyncClient(base_url=settings.VISION_URL, timeout=30.0)
        self.intel = httpx.AsyncClient(base_url=settings.INTELLIGENCE_URL, timeout=30.0)

    async def close(self):
        await self.scam.aclose()
        await self.vision.aclose()
        await self.intel.aclose()

    # ── Scam Intelligence: Audio ─────────────────────────────────────────────
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=False
    )
    async def analyze_audio(
        self, file_id: str, language: str = "auto",
        file_bytes: Optional[bytes] = None, filename: str = "audio.wav"
    ) -> Dict[str, Any]:
        logger.info("Calling scam-intelligence /audio", file_id=file_id)
        try:
            if file_bytes:
                files = {"file": (filename, file_bytes, "audio/wav")}
                resp = await self.scam.post("/audio", files=files)
            else:
                # No bytes: fallback immediately
                return self._mock_audio_result(file_id, language)

            if resp.status_code == 200:
                data = resp.json()
                # scam-intelligence /audio returns AudioAnalysisResult directly (no job_id)
                return data
            logger.warning("Audio service non-200", status=resp.status_code)
            return self._mock_audio_result(file_id, language)
        except Exception as e:
            logger.warning("Audio service call failed, using fallback", error=str(e))
            return self._mock_audio_result(file_id, language)

    # ── Scam Intelligence: Text ──────────────────────────────────────────────
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=False
    )
    async def analyze_text(self, text: str, language: str = "auto") -> Dict[str, Any]:
        logger.info("Calling scam-intelligence /text", text_length=len(text))
        try:
            resp = await self.scam.post("/text", json={"text": text, "language": language})
            if resp.status_code == 200:
                return resp.json()   # Returns TextAnalysisResult directly
            logger.warning("Text service non-200", status=resp.status_code)
            return self._mock_text_result(text)
        except Exception as e:
            logger.warning("Text service call failed, using fallback", error=str(e))
            return self._mock_text_result(text)

    # ── Scam Intelligence: URL ───────────────────────────────────────────────
    async def analyze_url(self, url: str) -> Dict[str, Any]:
        logger.info("Calling scam-intelligence /url", url=url)
        try:
            resp = await self.scam.post("/url", params={"url": url})
            if resp.status_code == 200:
                return resp.json()
            return {"url": url, "overall_risk_score": 0.0, "risk_level": "LOW", "reasons": []}
        except Exception as e:
            logger.warning("URL analysis failed", error=str(e))
            return {"url": url, "overall_risk_score": 0.0, "risk_level": "LOW", "reasons": []}

    # ── Vision: Image (general analysis) ─────────────────────────────────────
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=False
    )
    async def analyze_image(
        self, file_id: str, file_bytes: Optional[bytes] = None,
        filename: str = "image.png", mode: str = "general"
    ) -> Dict[str, Any]:
        """
        mode = "general" → POST /image (GeneralImageAnalysisResult)
        mode = "currency" → POST /currency (CurrencyAnalysisResult)
        mode = "document" → POST /document (DocumentAnalysisResult)
        """
        logger.info("Calling vision service", file_id=file_id, mode=mode)
        endpoint = {"currency": "/currency", "document": "/document", "ocr": "/ocr"}.get(mode, "/image")
        try:
            if file_bytes:
                files = {"file": (filename, file_bytes, "image/png")}
                resp = await self.vision.post(endpoint, files=files)
            else:
                return self._mock_vision_result(file_id)

            if resp.status_code == 200:
                return resp.json()
            logger.warning("Vision service non-200", status=resp.status_code, endpoint=endpoint)
            return self._mock_vision_result(file_id)
        except Exception as e:
            logger.warning("Vision service call failed, using fallback", error=str(e))
            return self._mock_vision_result(file_id)

    # ── Intelligence Engine: Fuse ─────────────────────────────────────────────
    async def fuse_intelligence(
        self, case_id: str,
        scam_result: Optional[dict] = None,
        vision_result: Optional[dict] = None,
        user_report: Optional[dict] = None,
    ) -> Dict[str, Any]:
        logger.info("Calling intelligence /fuse", case_id=case_id)
        try:
            payload = {
                "case_id": case_id,
                "scam_result": scam_result or {},
                "vision_result": vision_result or {},
                "user_report": user_report or {"priority": "medium"}
            }
            resp = await self.intel.post("/fuse", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                # Intelligence engine wraps in {"job_id": ..., "status": ..., "result": {...}}
                return data.get("result", data)
            logger.warning("Intelligence fuse non-200", status=resp.status_code)
            return self._mock_intelligence_result(case_id)
        except Exception as e:
            logger.warning("Intelligence service call failed, using fallback", error=str(e))
            return self._mock_intelligence_result(case_id)

    # ── Intelligence Engine: Graph Query ──────────────────────────────────────
    async def query_graph(self, entity_type: str, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        try:
            resp = await self.intel.post("/graph/query", json={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "depth": depth
            })
            if resp.status_code == 200:
                return resp.json()
            return {"nodes": [], "edges": [], "clusters": []}
        except Exception as e:
            logger.warning("Graph query failed", error=str(e))
            return {"nodes": [], "edges": [], "clusters": []}

    # ── Intelligence Engine: Evidence Generate ────────────────────────────────
    async def generate_evidence(self, case_id: str, format: str = "json") -> Dict[str, Any]:
        try:
            resp = await self.intel.post("/evidence/generate", json={"case_id": case_id, "format": format})
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as e:
            logger.warning("Evidence generation failed", error=str(e))
            return {}

    # ── Fallback mock responses ───────────────────────────────────────────────
    def _mock_audio_result(self, file_id: str, language: str) -> Dict[str, Any]:
        return {
            "transcript": "Hello, this is CBI officer. Your Aadhaar has been flagged in money laundering...",
            "language": language,
            "duration_seconds": 45.2,
            "overall_risk_score": 0.94,
            "digital_arrest_score": 0.96,
            "risk_level": "CRITICAL",
            "identifiers": {"phone_numbers": [], "upi_ids": [], "urls": [], "email_addresses": [], "bank_account_like": []},
            "indicators": ["authority_impersonation", "urgency_pressure", "financial_demand"],
            "explanation": "Mock: Caller impersonates CBI officer, demands money to avoid digital arrest."
        }

    def _mock_text_result(self, text: str) -> Dict[str, Any]:
        return {
            "original_text": text,
            "detected_language": "en",
            "overall_risk_score": 0.88,
            "digital_arrest_score": 0.85,
            "phishing_score": 0.3,
            "urgency_score": 0.8,
            "isolation_score": 0.5,
            "risk_level": "HIGH",
            "identifiers": {"phone_numbers": [], "upi_ids": [], "urls": [], "email_addresses": [], "bank_account_like": []},
            "scam_indicators": [{"category": "digital_arrest_impersonation", "matched_phrase": "CBI", "similarity_score": 0.91}],
            "explanation": "Mock: High risk fraudulent text message detected."
        }

    def _mock_vision_result(self, file_id: str) -> Dict[str, Any]:
        return {
            "overall_risk_score": 0.15,
            "risk_level": "LOW",
            "verdict": "NO_COUNTERFEIT_DETECTED",
            "authenticity_confidence_score": 85.0,
            "forgery_analysis": {"forgery_suspicion_score": 5.0, "is_likely_tampered": False}
        }

    def _mock_intelligence_result(self, case_id: str) -> Dict[str, Any]:
        return {
            "case_id": case_id,
            "risk_level": "high",
            "overall_score": 0.82,
            "linked_cases": [],
            "network_analysis": {
                "cluster_id": None,
                "size": 1,
                "central_entities": [],
                "pattern": "emerging_pattern",
                "jurisdictions": []
            },
            "evidence_package": {
                "pdf_url": None,
                "json_url": None,
                "includes": []
            },
            "recommendations": {
                "citizen": ["Do not share OTPs, PINs, or passwords with anyone.", "Call National Cybercrime Helpline 1930."],
                "officer": ["Cross-reference caller identifiers against fraud database."],
                "analyst": ["Expand graph traversal to identify mule network."]
            }
        }
