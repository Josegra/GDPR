# Project Documentation: Automated Data Retention Management (GDPR)

**Table of Contents**

1.  [Executive Summary](#1-executive-summary)
2.  [Purpose & Legal Basis (GDPR)](#2-purpose--legal-basis-gdpr)
3.  [Scope & Data Types Affected](#3-scope--data-types-affected)
4.  [Technical Architecture & Component Roles](#4-technical-architecture--component-roles)
    * [4.1. Azure Data Factory (ADF)](#41-azure-data-factory-adf)
    * [4.2. Azure Databricks](#42-azure-databricks)
5.  [Control, Audit & Reporting Mechanisms](#5-control-audit--reporting-mechanisms)
6.  [Security & GDPR Compliance Aspects](#6-security--gdpr-compliance-aspects)
7.  [Key Parameters](#7-key-parameters)

---

## 1. Executive Summary

This project implements an automated solution for **data retention management**, focusing on the timely **deletion of personal data** from various storage systems. By ensuring data is not held longer than necessary, the system supports compliance with the **General Data Protection Regulation (GDPR)**, particularly the principle of **storage limitation**. The core logic is executed within an **Azure Databricks notebook** and its operations are robustly orchestrated and monitored by **Azure Data Factory (ADF)**.

## 2. Purpose & Legal Basis (GDPR)

* **Purpose:** The primary goal is to enforce data retention policies by automatically identifying and removing data that has surpassed its defined storage period. This process is crucial for minimizing data exposure and reducing the risks associated with unnecessary data hoarding.
* **Legal Basis:** The processing (deletion) of data by this system is performed to fulfill a **legal obligation** (GDPR Article 6.1.c). Specifically, it addresses the requirement of GDPR Article 5.1.e, which states that personal data shall be "kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed."

## 3. Scope & Data Types Affected

* **Scope:** The solution targets **data containers** – specifically, files residing in **Azure Data Lake Storage** and records within **Hive/Spark tables** managed by Databricks. These containers are presumed to hold personal data.
* **Key Data for Retention Logic:** The script does not directly interpret the "personal" nature of data within files/records. Instead, it relies on metadata to apply retention rules:
    * **File/Table Name:** Used for identification and context.
    * **Subsidiary/Country Code:** Allows for distinct retention policies based on geographical or organizational entities.
    * **Data Timestamp/Date Column:** The crucial element for determining if data has exceeded its retention period.

## 4. Technical Architecture & Component Roles

The solution leverages key Azure services for a scalable and reliable data retention pipeline:

### 4.1. Azure Data Factory (ADF)

Acts as the central orchestrator for the entire data retention process.

* **Pipelines:** ADF pipelines are designed with **conditional activities (IF statements)**. These conditions evaluate incoming parameters (e.g., presence of `folder_path` or `table_name`) to dynamically determine whether the current run should target Data Lake files or Hive/Spark tables.
* **Parameter Passing:** ADF seamlessly passes user-defined or dynamic pipeline parameters (e.g., `table_name`, `folder_path`, `ad_hoc_months`) as arguments to the Databricks notebook. This allows for flexible and reusable execution of the retention logic across different datasets.
* **Scheduled Triggers:** ADF pipelines can be scheduled to run at predefined intervals (e.g., daily, weekly), ensuring consistent and timely application of retention policies.

### 4.2. Azure Databricks

The computational engine where the core data retention logic resides.

* **Python Notebook (`/Common/GDPR_RetentionPeriod`):** This notebook is the heart of the solution.
    * It receives input parameters from ADF via `dbutils.widgets`.
    * It reads pre-defined **retention dictionaries** (e.g., from an external SQL database, as indicated by `readSqlSeverDatabaseFrom`) that map subsidiary or country codes to specific retention periods (`RetentionPeriod`).
    * It calculates a **"Cut-Off Date" (`CutOffDate`)**. This date is either derived from the `ad_hoc_months` parameter (if an ad-hoc period is provided) or from the `RetentionPeriod` fetched from the retention dictionaries, subtracting the defined months from the current date.
    * **Deletion Logic:**
        * **For Data Lake Files:** The script uses `dbutils.fs.rm(file_path, True)` to delete files in Azure Data Lake Storage whose internal date (extracted from the file name based on `data_format`) is older than the `CutOffDate`. The `True` flag ensures recursive deletion for directories if applicable.
        * **For Hive/Spark Tables:** The script constructs and executes SQL `TRUNCATE TABLE {table_name} WHERE {date_column_name} < '{CutOffDate}'` statements. This efficiently removes records from the specified table where the date in the `date_column_name` is older than the `CutOffDate`.

## 5. Control, Audit & Reporting Mechanisms

Robust logging and reporting are critical for demonstrating GDPR compliance and providing operational oversight:

* **Centralized Log Table (`risk_compliance_gdpr.gdpr_log`):**
    * Every execution of the retention process, whether successful or failed, is meticulously logged into this dedicated Hive/Spark table.
    * Logged details include: `ValueDate` (execution date), `fileName`/`tableName` (the data asset processed), `SubsidiaryCode`, `RetentionPeriod` applied, `CutOffDate` used, `Result` (e.g., "EXECUTED CORRECTLY", "Date is not correct"), and `AffectedRows` (number of files/records deleted).
    * This detailed record provides an essential audit trail, crucial for **accountability** (GDPR Article 5.2).
* **Automated Email Notifications:**
    * Upon completion of the retention process, particularly when `process` is set to "Email," the script generates an HTML report directly from the `gdpr_log` table.
    * This report is then automatically sent via email to pre-configured recipients (e.g., `email_toaddr`, `email_ccaddr`), providing timely updates on the success, failures, and scope of each retention run.

## 6. Security & GDPR Compliance Aspects

* **Azure Platform Security:** The solution benefits from the inherent security features of the Azure platform:
    * **Role-Based Access Control (RBAC):** Access to ADF pipelines, Databricks workspaces, and Data Lake Storage accounts is strictly controlled through Azure RBAC, ensuring only authorized identities can deploy, run, or modify the retention process.
    * **Network Security:** Communication between ADF, Databricks, and Data Lake occurs securely within the Azure network.
    * **Activity Logging & Auditing:** All activities within ADF and Databricks are logged in Azure Monitor and Azure Log Analytics, providing a comprehensive audit trail for security and compliance purposes.
* **Contribution to Data Subject Rights:** By implementing automated data deletion based on retention periods, the system directly supports the organization's ability to comply with the **right to erasure ("right to be forgotten")** (GDPR Article 17). It ensures that personal data is not retained beyond its necessary purpose, which is a prerequisite for effective exercise of this right.
* **Defined Responsibilities:**
    * **Data Controller:** The organization deploying and utilizing this solution, as it determines the purposes and means of the data processing (including retention and deletion).
    * **Data Processor:** Microsoft Azure (ADF, Databricks, Data Lake) acts as a data processor by providing the infrastructure and services.
    * **Administrators/Operators:** Personnel responsible for configuring, monitoring, and maintaining the ADF pipelines and Databricks notebooks, as well as reviewing logs and addressing any issues.

## 7. Key Parameters

The following are the primary parameters configured within the ADF pipeline, passed to and consumed by the Databricks notebook:

* `table_name`: (For Hive tables) Schema and name of the table(s) to process.
* `subsidiary_column_name`: (For Hive tables) Column containing subsidiary code.
* `date_column_name`: (For Hive tables) Column containing the date for retention calculation.
* `folder_path`: (For Data Lake files) Path to the folder containing files to be deleted.
* `file_name`: (For Data Lake files) Constant or pattern for file names.
* `data_format`: (For Data Lake files) Expected date format in file names (e.g., 'dd-MM-yyyy').
* `process`: Controls the notebook's execution flow (e.g., `"Hives"` for tables, `"Email"` for reporting). The file processing is often inferred by the presence of `folder_path` and `file_name`.
* `ad_hoc_months`: An optional integer specifying an ad-hoc retention period in months, overriding default policies.
* `is_ad_hoc`: Boolean flag indicating if `ad_hoc_months` is being used.
* `sub_or_country`: Determines if retention is based on subsidiary or country data.