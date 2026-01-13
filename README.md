# EUROBOND Inventory Management System

A robust, full-stack web application designed for managing product inventory with a focus on ease of use, security, and responsiveness across all devices. This system allows for real-time tracking of stock levels (SQM), user role management, and comprehensive audit logging.

## Project Overview

This application serves as a centralized platform for the EUROBOND team to monitor and update inventory data. It utilizes a Flask backend and an interactive frontend styled with Tailwind CSS, supporting both light and dark modes for an optimal user experience.

## Key Features

* **Responsive Dashboard**: A fully mobile-responsive interface featuring scrollable tabs and a fluid layout that adjusts for smartphones, tablets, and desktops.

* **Dynamic Inventory Management**: View, add, edit, and delete inventory items with specific fields for Item Code, Color, Grade, Batch No, SQM, and custom Remarks.

* **Advanced Filtering**: Multi-field search functionality allows users to filter the database by Item Code, Color, Grade, or Batch Number simultaneously.

* **Role-Based Access Control (RBAC)**:

  * **Director**: Full access to inventory, user management, and audit logs.

  * **Admin**: Can manage inventory and perform bulk CSV resets.

  * **Viewer**: Read-only access to the inventory dashboard.

* **Audit Logging**: Every sensitive action (logins, inventory changes, user creation) is recorded in a dedicated audit log for internal transparency and accountability.

* **CSV Data Reset**: Authorized administrators can bulk-update the entire database by uploading a standardized CSV file.

* **Theme Support**: Seamlessly switch between light and dark modes with persistent user preferences.

## Technical Stack

* **Backend**: Python 3.x, Flask

* **Database**: SQLite3 (relational database management)

* **Frontend**: HTML5, JavaScript (ES6+), Tailwind CSS

* **Authentication**: Werkzeug security (Secure password hashing)

## Directory Structure
