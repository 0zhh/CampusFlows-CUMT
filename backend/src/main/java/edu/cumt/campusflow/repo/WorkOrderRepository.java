package edu.cumt.campusflow.repo;

import edu.cumt.campusflow.model.WorkOrder;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface WorkOrderRepository extends JpaRepository<WorkOrder, String> {
    List<WorkOrder> findAllByOrderByBucketAsc();
    List<WorkOrder> findByStatusOrderByBucketAsc(String status);
}
