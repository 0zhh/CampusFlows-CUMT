package edu.cumt.campusflow.repo;

import java.util.List;
import edu.cumt.campusflow.model.SimulationRun;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SimulationRunRepository extends JpaRepository<SimulationRun, Long> {
    List<SimulationRun> findAllByOrderByCreatedAtDesc();
    List<SimulationRun> findByScenarioIdOrderByCreatedAtDesc(String scenarioId);
}