package edu.cumt.campusflow.repo;

import java.util.List;
import edu.cumt.campusflow.model.SimResult;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SimResultRepository extends JpaRepository<SimResult, SimResult.Key> {
    List<SimResult> findByRunIdOrderBySiteIdAscBucketAsc(Long runId);
}