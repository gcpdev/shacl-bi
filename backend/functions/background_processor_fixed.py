#!/usr/bin/env python3
"""
Fixed background processor for generating AI explanations asynchronously.
This service runs background threads to process violations and generate enhanced explanations.
"""

import threading
import time
import logging
from typing import List, Dict, Any, Optional
from queue import Queue, Empty
from dataclasses import dataclass
from datetime import datetime

from .phoenix_service import (
    load_vkg_from_virtuoso,
    generate_enhanced_explanation,
    cache_explanation,
    create_violation_signature,
    explanation_cache,
)
from .virtuoso_service import execute_sparql_query
from .xpshacl_engine.xpshacl_architecture import ConstraintViolation
import config

logger = logging.getLogger(__name__)


@dataclass
class ProcessingJob:
    """A job for background processing."""

    session_id: str
    violations: List[Dict[str, Any]]
    timestamp: datetime
    status: str = "queued"  # queued, processing, completed, failed


class BackgroundProcessor:
    """Manages background processing of violation explanations."""

    def __init__(self):
        self.job_queue = Queue()
        self.processing_jobs = {}  # session_id -> ProcessingJob
        self.completed_jobs = {}  # session_id -> ProcessingJob
        self.worker_thread = None
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        """Start the background processor."""
        if self.running:
            logger.warning("Background processor already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Background processor started")

    def stop(self):
        """Stop the background processor."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Background processor stopped")

    def submit_job(self, session_id: str, violations: List[Dict[str, Any]]) -> bool:
        """Submit a job for background processing."""
        with self._lock:
            if session_id in self.processing_jobs or session_id in self.completed_jobs:
                logger.warning(f"Job for session {session_id} already exists")
                return False

            job = ProcessingJob(
                session_id=session_id,
                violations=violations,
                timestamp=datetime.now(),
                status="queued",
            )

            self.processing_jobs[session_id] = job
            self.job_queue.put(job)
            logger.info(
                f"Submitted background job for session {session_id} with {len(violations)} violations"
            )
            return True

    def get_job_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a background job."""
        with self._lock:
            # Check processing jobs
            if session_id in self.processing_jobs:
                job = self.processing_jobs[session_id]
                return {
                    "status": job.status,
                    "timestamp": job.timestamp.isoformat(),
                    "violations_count": len(job.violations),
                }

            # Check completed jobs
            if session_id in self.completed_jobs:
                job = self.completed_jobs[session_id]
                return {
                    "status": job.status,
                    "timestamp": job.timestamp.isoformat(),
                    "violations_count": len(job.violations),
                }

            return None

    def _worker_loop(self):
        """Main worker loop for processing jobs."""
        logger.info("Background worker loop started")

        while self.running:
            try:
                # Get next job from queue (with timeout)
                job = self.job_queue.get(timeout=1)

                logger.info(f"Processing job for session {job.session_id}")
                job.status = "processing"

                # Process the job
                success = self._process_job(job)

                # Move job to completed
                job.status = "completed" if success else "failed"

                with self._lock:
                    if job.session_id in self.processing_jobs:
                        self.processing_jobs.pop(job.session_id)
                    self.completed_jobs[job.session_id] = job

                logger.info(
                    f"Completed job for session {job.session_id}, success: {success}"
                )

            except Empty:
                # No jobs in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in background worker: {e}", exc_info=True)

        logger.info("Background worker loop stopped")

    def _process_job(self, job: ProcessingJob) -> bool:
        """Process a single job."""
        try:
            logger.info(f"Starting processing job for session {job.session_id}")
            job.status = "processing"

            # Load VKG
            vkg = load_vkg_from_virtuoso()
            if not vkg:
                logger.error(f"Failed to load VKG for session {job.session_id}")
                return False

            # If no violations provided, fetch them from database
            violations_to_process = job.violations
            if not violations_to_process:
                logger.info(f"No violations provided in job, fetching from database for session {job.session_id}")
                violations_to_process = self._fetch_violations_from_db(job.session_id)

            logger.info(f"Processing {len(violations_to_process)} violations for session {job.session_id}")

            # Process each violation
            processed_count = 0
            for violation in violations_to_process:
                try:
                    # Normalize violation data to handle different field naming conventions
                    normalized_violation = self._normalize_violation_data(violation)

                    # Convert dictionary to ConstraintViolation object for signature generation
                    try:
                        violation_obj = ConstraintViolation.from_dict(normalized_violation)
                    except Exception as e:
                        logger.warning(f"Could not convert violation to ConstraintViolation object: {e}")
                        continue

                    # Check if we already have an enhanced explanation
                    signature = create_violation_signature(violation_obj)
                    if signature in explanation_cache:
                        logger.debug(
                            f"Explanation already cached for violation {signature}"
                        )
                        continue

                    # Generate enhanced explanation
                    logger.info(
                        f"Generating enhanced explanation for violation: {normalized_violation.get('constraint_id', 'Unknown')} in session {job.session_id}"
                    )
                    logger.info(f"Violation details: focus_node={normalized_violation.get('focus_node')}, message={normalized_violation.get('message', '')[:50]}...")

                    explanation = generate_enhanced_explanation(normalized_violation)

                    if explanation:
                        logger.info(f"Successfully generated enhanced explanation for violation in session {job.session_id}")
                        # Cache the explanation using the original dictionary format
                        cache_explanation(violation, explanation)
                        processed_count += 1
                    else:
                        logger.warning(f"Failed to generate enhanced explanation for violation in session {job.session_id}")

                except Exception as e:
                    logger.error(
                        f"Error processing violation in session {job.session_id}: {e}"
                    )
                    continue

            logger.info(
                f"Processed {processed_count} violations for session {job.session_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error processing job for session {job.session_id}: {e}", exc_info=True
            )
            return False

    def _normalize_violation_data(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize violation data to handle different field naming conventions."""
        normalized = violation.copy()

        # Handle different field names for compatibility
        if 'constraint_id' not in normalized and 'constraint_component' in normalized:
            normalized['constraint_id'] = normalized['constraint_component']

        if 'property_path' not in normalized and 'result_path' in normalized:
            normalized['property_path'] = normalized['result_path']

        if 'shape_id' not in normalized and 'source_shape' in normalized:
            normalized['shape_id'] = normalized['source_shape']

        # Ensure required fields exist
        if 'violation_type' not in normalized:
            normalized['violation_type'] = 'other'

        return normalized

    def _fetch_violations_from_db(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch violations from database for a given session."""
        try:
            from .virtuoso_service import execute_sparql_query
            import config

            validation_graph_uri = f"http://ex.org/ValidationReport/Session_{session_id}"

            violations_query = f"""
            SELECT ?focusNode ?resultMessage ?resultPath ?resultSeverity ?sourceConstraintComponent ?value ?sourceShape
            FROM <{validation_graph_uri}>
            WHERE {{
                ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                         <http://www.w3.org/ns/shacl#resultMessage> ?resultMessage ;
                         <http://www.w3.org/ns/shacl#resultSeverity> ?resultSeverity ;
                         <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?sourceConstraintComponent .
                OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#focusNode> ?focusNode . }}
                OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#resultPath> ?resultPath . }}
                OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#value> ?value . }}
                OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#sourceShape> ?sourceShape . }}
            }}
            """

            results = execute_sparql_query(violations_query)

            violations_data = []
            for result in results["results"]["bindings"]:
                violation = {
                    "focus_node": result.get("focusNode", {}).get("value", ""),
                    "message": result.get("resultMessage", {}).get("value", ""),
                    "property_path": result.get("resultPath", {}).get("value", ""),
                    "severity": result.get("resultSeverity", {}).get("value", ""),
                    "constraint_id": result.get("sourceConstraintComponent", {}).get(
                        "value", ""
                    ),
                    "value": result.get("value", {}).get("value", ""),
                    "shape_id": result.get("sourceShape", {}).get("value", ""),
                    "violation_type": "other",
                }
                violations_data.append(violation)

            logger.info(
                f"Fetched {len(violations_data)} violations from database for session {session_id}"
            )
            return violations_data

        except Exception as e:
            logger.error(
                f"Error fetching violations from database for session {session_id}: {e}"
            )
            return []


# Global background processor instance
background_processor = BackgroundProcessor()


def start_background_processor():
    """Start the global background processor."""
    background_processor.start()


def stop_background_processor():
    """Stop the global background processor."""
    background_processor.stop()


def submit_explanation_job(session_id: str, violations: List[Dict[str, Any]]) -> bool:
    """Submit a job for background explanation processing."""
    return background_processor.submit_job(session_id, violations)


def get_job_status(session_id: str) -> Optional[Dict[str, Any]]:
    """Get the status of a background explanation job."""
    return background_processor.get_job_status(session_id)