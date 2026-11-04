package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

/** 参数版本快照 */
@Entity
@Table(name = "param_version")
public class ParamVersion {
    @Id
    public String version;
    public LocalDateTime createdAt;
    public short observedCnt;
    public short publicCnt;
    public short assumedCnt;
    public short totalCnt;
    public String payload;
}