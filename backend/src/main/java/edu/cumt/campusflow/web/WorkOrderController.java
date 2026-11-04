package edu.cumt.campusflow.web;

import java.util.List;
import java.util.Map;

import edu.cumt.campusflow.model.WorkOrder;
import edu.cumt.campusflow.model.WorkOrderEvent;
import edu.cumt.campusflow.repo.WorkOrderEventRepository;
import java.time.LocalDateTime;
import edu.cumt.campusflow.repo.WorkOrderRepository;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/workorders")
public class WorkOrderController {

    private final WorkOrderRepository orders;
    private final WorkOrderEventRepository events;

    public WorkOrderController(WorkOrderRepository orders, WorkOrderEventRepository events) {
        this.orders = orders;
        this.events = events;
    }

    /** F2：工单状态流转流水 */
    @GetMapping("/{id}/events")
    public List<WorkOrderEvent> events(@PathVariable String id) {
        return events.findByWoIdOrderByAtTimeAsc(id);
    }

    @GetMapping
    public List<WorkOrder> list(@RequestParam(required = false) String status) {
        return status == null || status.isBlank()
                ? orders.findAllByOrderByBucketAsc()
                : orders.findByStatusOrderByBucketAsc(status);
    }

    /** 状态流转：open → doing → closed（也允许回退，便于演示复位） */
    @PatchMapping("/{id}")
    public WorkOrder update(@PathVariable String id, @RequestBody Map<String, String> body) {
        WorkOrder w = orders.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "工单不存在: " + id));
        String status = body.get("status");
        if (status == null || !List.of("open", "doing", "closed").contains(status)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "status 只能是 open/doing/closed");
        }
        String from = w.getStatus();
        if (!status.equals(from)) {
            w.setStatus(status);
            orders.save(w);
            WorkOrderEvent ev = new WorkOrderEvent();
            ev.woId = id;
            ev.fromStatus = from;
            ev.toStatus = status;
            ev.actor = body.getOrDefault("actor", "调度员");
            ev.atTime = LocalDateTime.now();
            ev.note = body.getOrDefault("note", "");
            events.save(ev);
        }
        return w;
    }

    /** 一键复位：全部回到 open 之前的状态（演示用） */
    @PostMapping("/reset")
    public List<WorkOrder> reset() {
        List<WorkOrder> all = orders.findAllByOrderByBucketAsc();
        for (int i = 0; i < all.size(); i++) {
            all.get(i).setStatus(i == 0 ? "open" : i == 1 ? "doing" : "closed");
        }
        return orders.saveAll(all);
    }
}
