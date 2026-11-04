package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import java.io.Serializable;
import java.time.LocalDateTime;

/** 取件码（站内唯一） */
@Entity
@Table(name = "pickup_code")
@IdClass(PickupCode.Key.class)
public class PickupCode {
    @Id
    public String siteId;
    @Id
    public String code;
    public String parcelId;
    public LocalDateTime issuedAt;

    public static class Key implements Serializable {
        public String siteId;
        public String code;
    }
}