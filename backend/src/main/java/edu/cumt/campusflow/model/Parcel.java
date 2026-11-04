package edu.cumt.campusflow.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

/** 包裹（演示抽样） */
@Entity
@Table(name = "parcel")
public class Parcel {
    @Id
    public String id;
    public String siteId;
    public String carrierCode;
    @Column(columnDefinition = "CHAR(1)")
    public String size;
    public String batchId;
    public LocalDateTime arrivedAt;
    public LocalDateTime shelvedAt;
    public LocalDateTime pickedAt;
    public String status;
}