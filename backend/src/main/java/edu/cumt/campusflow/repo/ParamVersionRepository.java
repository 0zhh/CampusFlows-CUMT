package edu.cumt.campusflow.repo;

import java.util.List;
import edu.cumt.campusflow.model.ParamVersion;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ParamVersionRepository extends JpaRepository<ParamVersion, String> {
    List<ParamVersion> findAllByOrderByCreatedAtDesc();
}