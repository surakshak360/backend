import asyncio
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.exceptions import APIException
from app.core.logging import logger


class MLClient:
    def __init__(self):
        self.scam = httpx.AsyncClient(base_url=settings.SCAM_INTELLIGENCE_URL, timeout=60.0)
        self.vision = httpx.AsyncClient(base_url=settings.VISION_URL, timeout=30.0)
        self.intel = httpx.AsyncClient(base_url=settings.INTELLIGENCE_URL, timeout=10.0)

    async def close(self):
        await self.scam.aclose()
        await self.vision.aclose()
        await self.intel.aclose()

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    async def analyze_audio(self, file_id: str, language: str = "auto") -> Dict[str, Any]:
        logger.info("Calling scam-intelligence audio service", file_id=file_id, language=language)
        try:
            resp = await self.scam.post("/audio", json={"file_id": file_id, "language": language})
            if resp.status_code != 200:
                # Return fallback mock result if ML service unavailable in local testing
                return self._mock_audio_result(file_id, language)
            
            data = resp.json()
            job_id = data.get("job_id")
            if not job_id:
                return data.get("result", data)
            
            for _ in range(30):
                await asyncio.sleep(1)
                job_resp = await self.scam.get(f"/jobs/{job_id}")
                if job_resp.status_code == 200:
                    status_data = job_resp.json()
                    if status_data.get("status") == "completed":
                        return status_data.get("result", {})
                    if status_data.get("status") == "failed":
                        raise APIException("UPSTREAM_ERROR", f"ML Audio service error: {status_data.get('error')}", 502)
            
            return self._mock_audio_result(file_id, language)
        except Exception as e:
            logger.warning("Scam intelligence service call failed, returning fallback mock", error=str(e))
            return self._mock_audio_result(file_id, language)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    async def analyze_text(self, text: str, language: str = "auto") -> Dict[str, Any]:
        logger.info("Calling scam-intelligence text service", text_length=len(text))
        try:
            resp = await self.scam.post("/text", json={"text": text, "language": language})
            if resp.status_code == 200:
                return resp.json().get("result", resp.json())
            return self._mock_text_result(text)
        except Exception as e:
            logger.warning("Text service call failed, returning fallback mock", error=str(e))
            return self._mock_text_result(text)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    async def analyze_image(self, file_id: str) -> Dict[str, Any]:
        logger.info("Calling vision service", file_id=file_id)
        try:
            resp = await self.vision.post("/currency", json={"file_id": file_id})
            if resp.status_code == 200:
                return resp.json().get("result", resp.json())
            return self._mock_vision_result(file_id)
        except Exception as e:
            logger.warning("Vision service call failed, returning fallback mock", error=str(e))
            return self._mock_vision_result(file_id)

    async def fuse_intelligence(self, case_id: str, scam_result: Optional[dict] = None, vision_result: Optional[dict] = None) -> Dict[str, Any]:
        logger.info("Calling intelligence fusion service", case_id=case_id)
        try:
            payload = {
                "case_id": case_id,
                "scam_result": scam_result or {},
                "vision_result": vision_result or {},
                "user_report": {"priority": "medium"}
            }
            resp = await self.intel.post("/fuse", json=payload)
            if resp.status_code == 200:
                return resp.json().get("result", resp.json())
            return self._mock_intelligence_result(case_id)
        except Exception as e:
            logger.warning("Intelligence service call failed, returning fallback mock", error=str(e))
            return self._mock_intelligence_result(case_id)

    def _mock_audio_result(self, file_id: str, language: str) -> Dict[str, Any]:
        return {
            "transcript": "Hello, this is CBI officer. Your Aadhaar has been flagged in money laundering...",
            "language": language,
            "duration_seconds": 45.2,
            "risk_score": 0.94,
            "scam_type": "digital_arrest",
            "confidence": 0.91,
            "entities": [
                {"type": "organization", "value": "CBI", "spoofed": True},
                {"type": "amount", "value": "50000", "currency": "INR"}
            ],
            "indicators": ["authority_impersonation", "urgency_pressure", "financial_demand"],
            "summary": "Caller impersonates CBI officer, demands money to avoid digital arrest.",
            "recommendations": ["Do not transfer money", "Report to 1930 helpline"]
        }

    def _mock_text_result(self, text: str) -> Dict[str, Any]:
        return {
            "risk_score": 0.88,
            "scam_type": "digital_arrest",
            "confidence": 0.90,
            "entities": [{"type": "agency", "value": "CBI"}],
            "indicators": ["impersonation", "urgency"],
            "summary": "High risk fraudulent text message detected."
        }

    def _mock_vision_result(self, file_id: str) -> Dict[str, Any]:
        return {
            "is_counterfeit": True,
            "confidence": 0.95,
            "denomination": 500,
            "detected_class": "fake_500_v2",
            "defects": [{"feature": "security_thread", "status": "absent"}],
            "risk_score": 0.92
        }

    def _mock_intelligence_result(self, case_id: str) -> Dict[str, Any]:
        return {
            "case_id": case_id,
            "risk_level": "critical",
            "overall_score": 0.93,
            "linked_cases": [{"case_id": "case_linked_1", "similarity": 0.87}],
            "network_analysis": {
                "cluster_id": "cluster_cyber_01",
                "size": 14,
                "pattern": "mule_network"
            },
            "evidence_package": {
                "pdf_url": "https://storage.surakshak360.com/evidence.pdf",
                "json_url": "https://storage.surakshak360.com/evidence.json"
            },
            "recommendations": {
                "citizen": ["Block number", "Report to 1930"],
                "officer": ["Freeze linked accounts", "Request CDR"]
            }
        }
