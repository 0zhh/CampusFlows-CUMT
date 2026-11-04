package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

/** 工单状态流转流水 */
@Entity
@Table(name = "workorder_event")
public class WorkOrderEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public String woId;
    public String fromStatus;
    public String toStatus;
    public String actor;
    public LocalDateTime atTime;
    public String note;
}