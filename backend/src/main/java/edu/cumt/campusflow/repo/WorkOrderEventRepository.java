package edu.cumt.campusflow.repo;

import java.util.List;
import edu.cumt.campusflow.model.WorkOrderEvent;
import org.springframework.data.jpa.repository.JpaRepository;

public interface WorkOrderEventRepository extends JpaRepository<WorkOrderEvent, Long> {
    List<WorkOrderEvent> findByWoIdOrderByAtTimeAsc(String woId);
}