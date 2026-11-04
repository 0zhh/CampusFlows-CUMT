package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** 储位：NULL 表示空位 */
@Entity
@Table(name = "slot")
public class Slot {
    @Id
    public String id;
    public String shelfId;
    public short tier;
    public Integer cellNo;
    public String parcelId;
}