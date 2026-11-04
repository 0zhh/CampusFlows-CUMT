package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

/** 一次仿真运行（历史） */
@Entity
@Table(name = "simulation_run")
public class SimulationRun {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public String scenarioId;
    public int seed;
    public String paramVersion;
    public LocalDateTime createdAt;
    @jakarta.persistence.Column(name = "peak_i")
    public int peakI;
    public int riskBuckets;
    public String note;
}