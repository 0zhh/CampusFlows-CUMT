package edu.cumt.campusflow.repo;

import edu.cumt.campusflow.model.Scenario;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ScenarioRepository extends JpaRepository<Scenario, String> {
}