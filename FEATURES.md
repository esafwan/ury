# URY Feature Documentation

This document provides a comprehensive overview of all features in the URY Restaurant Management System, organized by functional categories. Each feature includes a business-friendly description and location information.

---

## Table of Contents

1. [Core Setup & Configuration](#core-setup--configuration)
2. [Menu & Recipe Management](#menu--recipe-management)
3. [POS & Order Management](#pos--order-management)
4. [Table & Room Management](#table--room-management)
5. [Kitchen Display System (KDS)](#kitchen-display-system-kds)
6. [Billing & Payment](#billing--payment)
7. [Multi-Cashier Operations](#multi-cashier-operations)
8. [Reports & Analytics](#reports--analytics)
9. [Operational Alerts & Monitoring](#operational-alerts--monitoring)
10. [Printing & Hardware Integration](#printing--hardware-integration)
11. [Aggregator Integration](#aggregator-integration)
12. [User Management & Permissions](#user-management--permissions)
13. [Recommended Feature Enhancements](#recommended-feature-enhancements)
14. [Planned Innovations & Roadmap](#planned-innovations--roadmap)
15. [File Tracking](#file-tracking)
16. [Dependencies Summary](#dependencies-summary)

---

## Core Setup & Configuration

### Branch Configuration
**Location:** ERPNext Desk → Branch  
**Dependencies:** ERPNext, Frappe HR  
**Description:**  
Configure restaurant branches with user assignments, POS access controls, and aggregator platform settings. Manages which users can access POS for each branch and sets up delivery platform integrations with dedicated customers, price lists, and payment methods.

### URY Restaurant Setup
**Location:** ERPNext Desk → URY Restaurant  
**Dependencies:** ERPNext Branch, URY Menu  
**Description:**  
Central configuration for each restaurant outlet linking company, branch, and menu. Defines tax templates, invoice naming series, and supports room-wise and order-type-wise menu variations for flexible pricing strategies.

### POS Profile Configuration
**Location:** ERPNext Desk → POS Profile  
**Dependencies:** ERPNext POS Profile  
**Description:**  
Extended POS Profile configuration with URY-specific settings including printer management (network/QZ), role-based permissions, KOT settings, multiple cashier support, and operational restrictions like discount controls and daily closing requirements.

### URY Report Settings
**Location:** ERPNext Desk → URY Report Settings  
**Dependencies:** ERPNext  
**Description:**  
Configure daily Profit & Loss calculation parameters including extended hours support, buying price lists, direct/indirect expenses, employee costs, and material consumption tracking for accurate financial reporting.

---

## Menu & Recipe Management

### URY Menu
**Location:** ERPNext Desk → URY Menu  
**Dependencies:** ERPNext Items, Price Lists  
**Description:**  
Create and manage restaurant menus with item pricing, availability controls, and course categorization. Automatically syncs with ERPNext Price Lists and supports special dish highlighting and item disabling for flexible menu management.

### Menu Course Management
**Location:** ERPNext Desk → URY Menu Course  
**Dependencies:** URY Menu  
**Description:**  
Organize menu items by courses (Starters, Mains, Desserts, etc.) with serving priority indicators. Enables course-based menu filtering in POS and determines preparation order in Kitchen Display System when priority is enabled.

### Room-Wise Menu Configuration
**Location:** ERPNext Desk → URY Restaurant → Menu For Room  
**Dependencies:** URY Restaurant, URY Room, URY Menu  
**Description:**  
Assign different menus and price lists to specific restaurant rooms (e.g., VIP area, outdoor seating). Allows restaurants to offer premium pricing or different menus in designated areas while maintaining a single menu structure.

### Order Type-Wise Menu Configuration
**Location:** ERPNext Desk → URY Restaurant → Menu For Order Type  
**Dependencies:** URY Restaurant, URY Menu  
**Description:**  
Configure different menus and pricing for various order types (Dine-in, Takeaway, Delivery, Aggregator). Enables cashiers to see order-type-specific menus and pricing, supporting different pricing strategies for different service channels.

### Recipe Mapping via Bill of Materials
**Location:** ERPNext Desk → Item → BOM  
**Dependencies:** ERPNext BOM  
**Description:**  
Link menu items to recipes using ERPNext Bill of Materials for production planning and cost calculation. Supports nested BOM structures for complex recipes and integrates with daily P&L for accurate cost of goods sold calculations.

---

## POS & Order Management

### URY POS (Modern Web Application)
**Location:** Frontend → `/pos` (React/TypeScript)  
**Dependencies:** ERPNext, URY Backend APIs  
**Description:**  
Modern, responsive web-based Point of Sale application for order taking and billing. Supports multiple order types (Dine-in, Takeaway, Delivery, Aggregator), real-time menu display, table selection, customer management, and seamless integration with kitchen and billing systems.

### Order Taking & Modification
**Location:** Frontend → POS Application  
**Dependencies:** URY Order API, URY KOT  
**Description:**  
Create and modify customer orders with item selection, quantity adjustment, special instructions, and course sequencing. Real-time inventory checks prevent ordering unavailable items, and order modifications automatically generate updated KOTs for kitchen.

### Order Status Management
**Location:** Frontend → Orders Page  
**Dependencies:** POS Invoice, URY Order API  
**Description:**  
View and manage orders across different statuses (Draft, Unbilled, Paid, Consolidated, Cancelled). Search and filter orders by customer, invoice number, or mobile number. Supports order editing, cancellation with reason tracking, and payment processing.

### Past Order Search
**Location:** Backend → POS Extend API, Frontend → ERPNext POS  
**Dependencies:** POS Invoice  
**Description:**  
Search historical orders by customer name or invoice number with input validation and security controls. Enables quick retrieval of past transactions for customer service, refunds, or order verification purposes. Includes filtering by invoice status (Draft, To Bill) and room-based filtering for captains.

### ERPNext POS Integration & Extensions
**Location:** Frontend → ERPNext POS Interface  
**Dependencies:** ERPNext POS, Client Scripts  
**Description:**  
Extended ERPNext POS interface with URY-specific enhancements including order cancellation with reason tracking, order editing restrictions for billed table orders, comment management, discount application, and custom invoice display with table information. Provides seamless integration between ERPNext's standard POS and URY's restaurant-specific features.

### Customer Quick Entry
**Location:** Frontend → Customer Selection  
**Dependencies:** ERPNext Customer  
**Description:**  
Simplified customer creation form for quick entry during order taking. Streamlined fields focusing on customer name and mobile number, with automatic mobile number population when numeric input is detected. Hides unnecessary fields for faster customer onboarding.

### Quantity Edit Restrictions
**Location:** Frontend → POS Invoice Form  
**Dependencies:** POS Profile, POS Invoice  
**Description:**  
Restrict quantity editing for billed table orders and disable UOM/warehouse field editing in POS interface. Prevents accidental modifications to completed orders and maintains data integrity for accounting and reporting purposes.

### KOT Auto-Generation on Save
**Location:** Frontend → POS Invoice Form  
**Dependencies:** URY KOT Generate API  
**Description:**  
Automatically generate or update KOTs when POS Invoice is saved, comparing current items with previous items to create appropriate KOT types (New Order, Order Modified). Ensures kitchen always receives updated order information when orders are modified in ERPNext POS interface.

### Invoice Print Handling
**Location:** Frontend → POS Invoice Form  
**Dependencies:** QZ Tray, Network Printers, Print API  
**Description:**  
Comprehensive invoice printing system supporting QZ Tray, network printers, and browser-based printing. Automatically updates invoice printed status and table occupancy when printing completes. Includes error handling and connection management for reliable printing operations.

### Item Add-Ons & Variants
**Location:** ERPNext Desk → Item → POS Variants Tab  
**Dependencies:** ERPNext Item, Item Add On, POS Item Variants  
**Description:**  
Configure item add-ons (complementary items) and POS-specific variants for menu items. Enables upselling opportunities and item customization options directly from the item master, separate from ERPNext's standard variant system.

### Customer Mobile Number Handling
**Location:** Frontend → Customer Quick Entry  
**Dependencies:** ERPNext Customer, Client Scripts  
**Description:**  
Smart customer creation that automatically populates mobile number field when numeric input is entered in customer name field. Simplifies customer entry process for walk-in customers and improves data consistency.

### Customer Management
**Location:** Frontend → POS Application, ERPNext Desk  
**Dependencies:** ERPNext Customer  
**Description:**  
Search and select customers from ERPNext database with global search integration. Create new customers on-the-fly, view customer favorite items based on order history, and maintain customer contact information for order tracking and marketing.

### Order Comments & Special Instructions
**Location:** Frontend → POS Application  
**Dependencies:** POS Invoice  
**Description:**  
Add order-level comments and item-specific special instructions that appear on KOTs and invoices. Enables communication between front-of-house and kitchen staff for customizations, dietary requirements, and special requests.

### Order Number Management
**Location:** Backend → POS Profile → KOT Settings  
**Dependencies:** POS Invoice  
**Description:**  
Generate sequential order numbers for invoices with optional daily reset functionality. Provides easy reference for staff and customers, separate from invoice numbering, for quick order identification and tracking.

---

## Table & Room Management

### URY Room Configuration
**Location:** ERPNext Desk → URY Room  
**Dependencies:** URY Restaurant  
**Description:**  
Define restaurant layout areas (indoor, outdoor, VIP, etc.) with printer configurations for room-specific KOT and bill printing. Organizes tables by location and enables room-based menu and pricing strategies.

### URY Table Management
**Location:** ERPNext Desk → URY Table  
**Dependencies:** URY Restaurant, URY Room  
**Description:**  
Create and manage restaurant tables with seating capacity, minimum seating requirements, and visual shape indicators. Tracks table occupancy status, latest order time, and supports takeaway table designation for non-dining orders.

### Table Selection & Status
**Location:** Frontend → Table View  
**Dependencies:** URY Table API  
**Description:**  
Visual table layout display showing table availability, occupancy status, and order information. Click-to-select interface for quick table assignment, with real-time status updates and room-based filtering.

### Table Transfer
**Location:** Backend → URY Order API  
**Dependencies:** POS Invoice, URY Table  
**Description:**  
Transfer active orders between tables within the same room. Automatically updates table occupancy status, invoice table reference, and KOT table information while maintaining order continuity.

### Table Attention Indicator
**Location:** Frontend → Table View, POS Profile  
**Dependencies:** URY Table, POS Profile  
**Description:**  
Visual indicator for tables requiring attention based on configurable time thresholds. Helps staff identify tables that may need service, refills, or check-ins, improving customer service efficiency.

---

## Kitchen Display System (KDS)

### Kitchen Display System (URYMosaic)
**Location:** Frontend → `/URYMosaic/Production%20Unit%20Name` (Vue.js)  
**Dependencies:** URY KOT, URY Production Unit  
**Description:**  
Web-based Kitchen Display System showing real-time order queues for kitchen staff. Displays KOTs organized by production unit, order status, and preparation priority. Supports multiple kitchens with dedicated displays per production unit.

### Production Unit Management
**Location:** ERPNext Desk → URY Production Unit  
**Dependencies:** POS Profile, Item Groups  
**Description:**  
Configure multiple kitchen stations or production units, each with assigned item groups and printer settings. Enables routing of orders to specific kitchens based on item type (e.g., bar, grill, dessert station).

### KOT Generation & Routing
**Location:** Backend → URY KOT Generate API  
**Dependencies:** POS Invoice, URY Production Unit  
**Description:**  
Automatically generate Kitchen Order Tickets when orders are placed or modified. Routes KOTs to appropriate production units based on item groups, supports multiple KOT types (New Order, Modified, Cancelled, Duplicate), and includes course-based sequencing.

### Real-Time KOT Updates
**Location:** Backend → URY KOT Display API, WebSocket  
**Dependencies:** URY KOT, Frappe Realtime  
**Description:**  
Live synchronization of KOT status changes across all connected devices. Updates appear instantly on KDS screens when orders are placed, modified, or status changes occur, ensuring kitchen staff always see current order information.

### KOT Status Management
**Location:** Frontend → KDS Interface  
**Dependencies:** URY KOT API  
**Description:**  
Track KOT preparation status (Ready For Prepare, Preparing, Ready, Served) with timestamps. Kitchen staff can update status as items are prepared, enabling real-time order tracking and service coordination.

### KOT Delay Alerts
**Location:** Backend → URY KOT Notification API  
**Dependencies:** URY KOT, POS Profile  
**Description:**  
Automated notifications sent to designated roles when KOTs exceed configured warning time thresholds. Helps managers identify delayed orders and take corrective action to maintain service quality.

### KOT Audio Alerts
**Location:** Backend → URY KOT, POS Profile  
**Dependencies:** URY KOT  
**Description:**  
Play audio alerts when new KOTs are displayed on KDS. Configurable sound files help kitchen staff notice new orders immediately, especially useful in busy environments.

### KOT Reprint
**Location:** Backend → URY KOT Reprint API  
**Dependencies:** URY KOT, Printer Settings  
**Description:**  
Reprint KOTs for lost or damaged tickets. Maintains order accuracy and enables kitchen operations to continue smoothly when physical tickets are misplaced.

### KOT Validation & Auto-Generation
**Location:** Backend → URY KOT Validation API  
**Dependencies:** POS Invoice, URY KOT  
**Description:**  
Background validation process that automatically creates KOTs for invoices that were created without KOTs due to system errors or timing issues. Ensures all orders have corresponding KOTs for kitchen operations.

### KOT Cancellation & Verification
**Location:** Frontend → KDS Interface, Backend → URY KOT API  
**Dependencies:** URY KOT  
**Description:**  
Handle cancelled orders with verification workflow. Kitchen staff can confirm cancellation of items, preventing preparation of cancelled orders and maintaining accurate order tracking.

### Production Time Tracking
**Location:** Backend → URY KOT  
**Dependencies:** URY KOT  
**Description:**  
Automatically calculate and record time taken from order placement to service completion. Provides data for performance analysis and helps identify bottlenecks in kitchen operations.

---

## Billing & Payment

### Invoice Generation
**Location:** Backend → URY Order API  
**Dependencies:** ERPNext POS Invoice  
**Description:**  
Create POS Invoices automatically when orders are placed, linked to ERPNext accounting and inventory systems. Supports multiple order types, tax calculations, and integrates with stock management for real-time inventory updates.

### Payment Processing
**Location:** Frontend → Payment Dialog  
**Dependencies:** POS Invoice, Mode of Payment  
**Description:**  
Process payments with support for multiple payment methods in a single transaction (e.g., part cash, part card). Calculates totals, taxes, and change amounts, with integration to ERPNext payment modes and accounting entries. Note: This is split payment method, not split billing - a single invoice can be paid using multiple payment methods.

### Discount Management
**Location:** Frontend → Payment Dialog, POS Profile  
**Dependencies:** POS Invoice  
**Description:**  
Apply percentage-based discounts to orders with role-based permission controls. Configurable discount enablement per POS Profile, ensuring only authorized staff can apply discounts.

### Invoice Printing
**Location:** Frontend → Orders Page, Backend → Print API  
**Dependencies:** POS Invoice, Printer Settings  
**Description:**  
Print customer invoices using configured network printers or QZ printing. Supports multiple print formats, room-specific printer routing, and reprint functionality for customer receipts.

### Network Printer Selection
**Location:** Backend → URY Print API  
**Dependencies:** Network Printer Settings  
**Description:**  
Select specific network printers for invoice printing at the time of printing. Enables flexible printer routing when multiple printers are available or when printer assignments need to be changed dynamically.

### QZ Certificate Management
**Location:** Backend → URY Print API  
**Dependencies:** QZ Tray, Certificate File  
**Description:**  
Manage QZ Tray certificate for secure printer communication. Handles certificate validation and signature promises required for QZ printing functionality.

### Print Format Selection
**Location:** Backend → URY Print API  
**Dependencies:** ERPNext Print Format  
**Description:**  
Select and apply different print formats for invoices and KOTs at print time. Supports multiple format options for different business needs and printer types.

### Pre-Billing Checklists
**Location:** Backend → POS Profile Restrictions  
**Dependencies:** ERPNext Custom Scripts  
**Description:**  
Enforce compliance checks before billing, such as stock verification and hygiene checklists. Ensures operational standards are met before order completion and payment processing.

### Invoice Status Management
**Location:** Backend → POS Invoice  
**Dependencies:** ERPNext POS Invoice  
**Description:**  
Track invoice lifecycle from draft to paid to consolidated. Supports invoice cancellation with reason tracking, return processing, and consolidation for accounting purposes.

---

## Multi-Cashier Operations

### Multiple Cashier Configuration
**Location:** ERPNext Desk → POS Profile → Multiple Cashier Configuration  
**Dependencies:** POS Profile, URY User  
**Description:**  
Enable multiple cashiers to operate under a single POS Profile with individual transaction tracking. Configure main cashier and sub-cashiers, assign rooms to cashiers, and manage access controls per cashier.

### POS Opening Entry
**Location:** ERPNext Desk → POS Opening Entry  
**Dependencies:** ERPNext POS Opening Entry, Multiple Rooms  
**Description:**  
Open POS sessions with cash register amounts and room assignments. Main cashier opens first, followed by sub-cashiers. Validates previous day closing before allowing new opening when daily closing is required.

### Sub POS Closing
**Location:** ERPNext Desk → Sub POS Closing  
**Dependencies:** POS Opening Entry, POS Invoice  
**Description:**  
Reconcile individual cashier transactions separately before main POS closing. Sub-cashiers create closing entries for their transactions, enabling individual accountability and cash reconciliation per cashier.

### POS Closing Entry
**Location:** ERPNext Desk → POS Closing Entry  
**Dependencies:** ERPNext POS Closing Entry, Sub POS Closing  
**Description:**  
Main cashier creates final POS closing entry after all sub-cashiers have closed. Consolidates all transactions, reconciles cash and payment modes, and completes the daily POS cycle.

### Daily POS Closing Validation
**Location:** Backend → POS Profile, URY POS API  
**Dependencies:** POS Opening Entry  
**Description:**  
Enforce daily POS closing requirement, preventing new POS opening until previous day is closed. Ensures proper cash reconciliation and accounting accuracy by requiring sequential daily closures.

### Cashier-Specific Order Views
**Location:** Frontend → Orders Page  
**Dependencies:** POS Invoice, User Permissions  
**Description:**  
Filter and display orders by assigned cashier, enabling individual cashier performance tracking and transaction management. Supports cashier-specific order history and reconciliation.

---

## Reports & Analytics

### Daily Profit & Loss Report
**Location:** ERPNext Desk → URY Daily P & L  
**Dependencies:** URY Report Settings, POS Invoice, BOM, Employee Attendance  
**Description:**  
Comprehensive daily financial report calculating revenue, cost of goods sold (using BOM and buying prices), direct expenses (materials, utilities), indirect expenses, employee costs (from attendance), and net profit. Provides actionable insights for daily operations.

### Today's Sales Report
**Location:** ERPNext Desk → Report → Today's Sales  
**Dependencies:** POS Invoice  
**Description:**  
Real-time sales summary for current day including total revenue, order count, average bill value, and payment method breakdown. Quick reference for daily performance monitoring.

### Daywise Sales Report
**Location:** ERPNext Desk → Report → Daywise Sales  
**Dependencies:** POS Invoice  
**Description:**  
Compare sales performance across multiple days with trend analysis. Helps identify peak days, seasonal patterns, and performance variations for strategic planning.

### Item-Wise Sales Report
**Location:** ERPNext Desk → Report → Item Wise Sales  
**Dependencies:** POS Invoice Item  
**Description:**  
Analyze sales performance by individual menu items including quantity sold, revenue generated, and popularity ranking. Identifies best-sellers and slow-moving items for menu optimization.

### Employee Sales Report
**Location:** ERPNext Desk → Report → Employee Sales  
**Dependencies:** POS Invoice, Employee  
**Description:**  
Track sales performance by employee (captain/waiter) including order count, total sales, and average order value. Enables performance evaluation and incentive calculations.

### Employee Item-Wise Sales Report
**Location:** ERPNext Desk → Report → Employee Item Wise Sales  
**Dependencies:** POS Invoice, Employee  
**Description:**  
Detailed breakdown of items sold by each employee, useful for identifying upselling performance, product knowledge, and training needs.

### Customer Data Report
**Location:** ERPNext Desk → Report → Customer Data  
**Dependencies:** POS Invoice, Customer  
**Description:**  
Comprehensive customer analytics including visit frequency, total spending, average order value, and favorite items. Supports customer relationship management and targeted marketing.

### Repeated Customers Report
**Location:** ERPNext Desk → Report → Repeated Customers  
**Dependencies:** POS Invoice, Customer  
**Description:**  
Identify loyal customers with multiple visits and high lifetime value. Helps prioritize customer retention efforts and loyalty program management.

### Service-Wise Sales Report
**Location:** ERPNext Desk → Report → Service Wise Sales  
**Dependencies:** POS Invoice  
**Description:**  
Compare sales performance across different order types (Dine-in, Takeaway, Delivery, Aggregator). Enables channel optimization and pricing strategy evaluation.

### Time-Wise Sales Report
**Location:** ERPNext Desk → Report → Time Wise Sales  
**Dependencies:** POS Invoice  
**Description:**  
Analyze sales patterns by time of day, identifying peak hours, slow periods, and optimal staffing requirements. Supports operational planning and resource allocation.

### Average Bill Value Report
**Location:** ERPNext Desk → Report → Average Bill Value  
**Dependencies:** POS Invoice  
**Description:**  
Calculate average transaction value across different time periods, order types, and customer segments. Tracks upselling effectiveness and pricing strategy impact.

### Month-Wise Sales Report
**Location:** ERPNext Desk → Report → Month Wise Sales  
**Dependencies:** POS Invoice  
**Description:**  
Long-term sales trend analysis by month, enabling seasonal pattern identification, growth tracking, and strategic planning for menu and pricing adjustments.

### Cancelled Invoices Report
**Location:** ERPNext Desk → Report → Cancelled Invoices  
**Dependencies:** POS Invoice  
**Description:**  
Track cancelled orders with reasons and frequency analysis. Identifies operational issues, customer dissatisfaction patterns, and areas for service improvement.

### Daywise Customer Details Report
**Location:** ERPNext Desk → Report → Daywise Customer Details  
**Dependencies:** POS Invoice, Customer  
**Description:**  
Detailed daily customer visit and transaction data for specific date ranges. Supports customer service inquiries and transaction verification.

### Daywise Invoices Report
**Location:** ERPNext Desk → Report → Daywise Invoices  
**Dependencies:** POS Invoice  
**Description:**  
Complete invoice listing for selected dates with all transaction details. Useful for daily reconciliation, audit trails, and detailed transaction analysis.

---

## Operational Alerts & Monitoring

### KOT Delay Notifications
**Location:** Backend → URY KOT Notification API  
**Dependencies:** URY KOT, POS Profile, Notification Recipients  
**Description:**  
Automated email and system notifications sent to designated roles when KOTs exceed configured warning times. Helps managers identify and address kitchen delays proactively.

### Unclosed Bills Alert
**Location:** Frontend → Table View, Backend → URY Table  
**Dependencies:** POS Invoice, URY Table  
**Description:**  
Visual indicators for tables with unclosed bills exceeding attention time thresholds. Alerts staff to follow up with customers and ensure timely billing.

### KOT Not Started Alert
**Location:** Backend → URY KOT, KDS  
**Dependencies:** URY KOT  
**Description:**  
Monitor KOTs that remain in "Ready For Prepare" status beyond expected timeframes. Identifies potential kitchen workflow issues or missed orders.

### Excessive Cancellation Monitoring
**Location:** Backend → POS Invoice, Reports  
**Dependencies:** POS Invoice  
**Description:**  
Track cancellation rates and patterns through reports. Identifies potential issues with menu items, service quality, or operational processes.

### Real-Time Operational Dashboard
**Location:** Frontend → Various Views  
**Dependencies:** Multiple APIs  
**Description:**  
Live monitoring of restaurant operations including table status, active orders, kitchen queue, and service times. Provides managers with real-time visibility for quick decision-making.

---

## Printing & Hardware Integration

### Network Printer Support
**Location:** ERPNext Desk → Network Printer Settings, POS Profile, URY Room, URY Production Unit  
**Dependencies:** CUPS (Common Unix Printing System)  
**Description:**  
Configure network printers for invoice and KOT printing. Supports room-specific and production-unit-specific printer routing, enabling automatic printing to appropriate locations.

### QZ Tray Printing
**Location:** Frontend → Print API, POS Profile  
**Dependencies:** QZ Tray Software, Certificate File  
**Description:**  
Print directly to local printers using QZ Tray software with certificate-based authentication. Supports Windows, macOS, and Linux systems for flexible printer deployment.

### KOT Print Format Configuration
**Location:** ERPNext Desk → POS Profile, URY Production Unit  
**Dependencies:** ERPNext Print Format  
**Description:**  
Configure custom print formats for Kitchen Order Tickets with item details, special instructions, table information, and order timing. Supports multiple formats for different kitchen stations.

### Invoice Print Format Configuration
**Location:** ERPNext Desk → POS Profile  
**Dependencies:** ERPNext Print Format  
**Description:**  
Customize customer invoice print formats with branding, itemization, tax breakdown, and payment details. Supports multiple formats for different business needs.

### Room-Wise Printer Routing
**Location:** ERPNext Desk → URY Room  
**Dependencies:** Network Printer Settings  
**Description:**  
Assign specific printers to restaurant rooms for automatic routing of bills and KOTs. Ensures orders print at the correct location based on table assignment.

### Production Unit Printer Routing
**Location:** ERPNext Desk → URY Production Unit  
**Dependencies:** Network Printer Settings  
**Description:**  
Configure printers for each production unit to automatically print KOTs for items assigned to that kitchen station. Supports multi-kitchen operations with dedicated printing.

### Block Takeaway KOT Printing
**Location:** ERPNext Desk → URY Production Unit  
**Dependencies:** URY KOT  
**Description:**  
Option to prevent takeaway order KOTs from printing at specific production units. Useful for kitchens that don't handle takeaway orders or have separate preparation areas.

---

## Aggregator Integration

### Aggregator Platform Configuration
**Location:** ERPNext Desk → Branch → Aggregator Settings  
**Dependencies:** ERPNext Customer, Price List, Mode of Payment  
**Description:**  
Configure manual tracking for food delivery aggregator platforms (Swiggy, Zomato, etc.). Set up dedicated customers, price lists, and payment methods for each platform with optional tax exclusion. Note: This is manual tracking only - there is no automated API integration with aggregator platforms.

### Aggregator Order Processing
**Location:** Frontend → POS Application → Aggregator Order Type  
**Dependencies:** Aggregator Settings, POS Invoice  
**Description:**  
Manually process orders from aggregator platforms by selecting the aggregator order type. Applies platform-specific pricing and menu display based on configured aggregator settings. Orders must be manually entered into the system.

### Aggregator Invoice Series
**Location:** ERPNext Desk → URY Restaurant  
**Dependencies:** POS Invoice  
**Description:**  
Dedicated invoice numbering series for aggregator orders, enabling easy identification and separate reporting of delivery platform transactions.

### Aggregator Order ID Tracking
**Location:** Backend → POS Invoice  
**Dependencies:** POS Invoice  
**Description:**  
Manually store aggregator-provided order IDs with invoices for order tracking and reconciliation. This field allows manual entry of external platform order IDs for reference purposes.

### Aggregator Tax Configuration
**Location:** ERPNext Desk → Branch → Aggregator Settings  
**Dependencies:** POS Invoice  
**Description:**  
Option to create aggregator invoices without taxes, supporting different tax handling requirements for delivery platforms. Configurable per aggregator platform.

---

## User Management & Permissions

### URY Role System
**Location:** ERPNext Desk → Role  
**Dependencies:** ERPNext Role, Permissions  
**Description:**  
Pre-defined roles (URY Manager, URY Captain, URY Cashier) with appropriate permissions for restaurant operations. Managers oversee operations, Captains handle table service, and Cashiers manage billing and payments.

### Role-Based Access Control
**Location:** ERPNext Desk → POS Profile → URY POS Restrictions  
**Dependencies:** ERPNext Role, Permissions  
**Description:**  
Configure role-based permissions for POS operations including billing access, table order restrictions, discount permissions, and order type editing. Ensures proper access control and operational compliance.

### User-Branch Assignment
**Location:** ERPNext Desk → Branch → URY User  
**Dependencies:** ERPNext Branch, User  
**Description:**  
Assign users to specific branches and rooms, controlling POS access and operational scope. Users can only access POS for assigned branches and rooms, ensuring proper access boundaries.

### Captain Transfer Permissions
**Location:** ERPNext Desk → POS Profile → Captain Transfer Role Permissions  
**Dependencies:** URY Order API  
**Description:**  
Designate roles with permission to transfer orders between captains. Users with these roles can also access all tables, enabling flexible order management for supervisors.

### Button-Level Permissions
**Location:** Backend → Button Permission API  
**Dependencies:** ERPNext Permissions  
**Description:**  
Control visibility and access to specific POS functions based on user roles. Enables fine-grained permission control for sensitive operations like discounts, cancellations, and order modifications.

### User Permissions for Records
**Location:** ERPNext Desk → User Permissions  
**Dependencies:** ERPNext User Permissions  
**Description:**  
Restrict access to specific POS Profiles and Branches using ERPNext User Permissions. Ensures users can only access authorized locations and configurations.

---

## Recommended Feature Enhancements

Based on analysis of modern restaurant management systems and industry best practices, here are top feature suggestions to bring URY in line with contemporary applications:

### 1. **Real-Time Order Tracking Dashboard**
**Priority:** High  
**Description:**  
Live dashboard showing all active orders, table status, kitchen queue, and service times in real-time. Visual indicators for orders approaching SLA, delayed KOTs, and bottleneck identification. Enables managers to proactively manage operations and improve service speed.

### 2. **Mobile App for Waitstaff**
**Priority:** High  
**Description:**  
Native mobile application (iOS/Android) for waitstaff to take orders tableside, update order status, process payments, and communicate with kitchen. Reduces order errors, improves service speed, and enables tableside payment processing.

### 3. **Customer Loyalty & Rewards Program**
**Priority:** High  
**Description:**  
Integrated loyalty program with points accumulation, tiered membership levels, and automated reward redemption. Track customer visit frequency, spending patterns, and offer personalized promotions. Increases customer retention and repeat visits.

### 4. **Online Ordering & Reservation System**
**Priority:** High  
**Description:**  
Customer-facing web portal and mobile app for placing orders online, making reservations, and pre-ordering. Integration with POS for seamless order flow, table management, and payment processing. Expands revenue channels beyond dine-in.

### 5. **Advanced Inventory Management**
**Priority:** Medium  
**Description:**  
Real-time inventory tracking with low-stock alerts, automatic reorder points, waste tracking, and recipe-based consumption calculation. Integration with suppliers for automated purchase orders. Reduces food waste and ensures ingredient availability.

### 6. **Staff Scheduling & Shift Management**
**Priority:** Medium  
**Description:**  
Automated staff scheduling based on sales forecasts, shift swapping, time tracking, and attendance management. Integration with payroll for accurate wage calculation. Optimizes labor costs and ensures adequate staffing.

### 7. **Customer Feedback & Review Management**
**Priority:** Medium  
**Description:**  
Post-dining feedback collection via SMS/email, review aggregation from multiple platforms, sentiment analysis, and response management. Helps improve service quality and manage online reputation.

### 8. **Dynamic Pricing & Promotions Engine**
**Priority:** Medium  
**Description:**  
Time-based pricing (happy hours, peak pricing), combo deals, flash sales, and personalized promotions based on customer history. Automated discount application and promotion tracking. Maximizes revenue during slow periods.

### 9. **Advanced Analytics & Business Intelligence**
**Priority:** Medium  
**Description:**  
Predictive analytics for sales forecasting, menu item performance prediction, customer lifetime value calculation, and profitability analysis by item/category/time. Data visualization dashboards for quick insights. Enables data-driven decision making.

### 10. **Multi-Location & Franchise Management**
**Priority:** Medium  
**Description:**  
Centralized management for multiple restaurant locations with consolidated reporting, standardized menu management, and location-specific configurations. Enables franchise operations with consistent operations across outlets.

### 11. **Delivery Management & Driver Tracking**
**Priority:** Medium  
**Description:**  
Delivery order assignment, driver tracking via GPS, delivery time estimation, and delivery status updates for customers. Integration with third-party delivery services or in-house delivery fleet management.

### 12. **Table Reservation & Waitlist Management**
**Priority:** Medium  
**Description:**  
Online table reservation system with availability calendar, automatic waitlist management, SMS/email confirmations, and no-show tracking. Optimizes table utilization and improves customer experience.

### 13. **Recipe Costing & Menu Engineering**
**Priority:** Low  
**Description:**  
Detailed recipe costing with ingredient-level cost tracking, menu engineering analysis (star, plowhorse, puzzle, dog categorization), and profitability optimization suggestions. Helps optimize menu for maximum profitability.

### 14. **Compliance & Food Safety Management**
**Priority:** Low  
**Description:**  
Food safety checklist management, temperature logging, expiration date tracking, and compliance reporting. Integration with health department requirements and audit trail maintenance.

### 15. **Social Media Integration**
**Priority:** Low  
**Description:**  
Social media posting automation, Instagram/Facebook menu integration, social media order placement, and social engagement tracking. Expands marketing reach and enables social commerce.

### 16. **Gift Card & Voucher Management**
**Priority:** Low  
**Description:**  
Digital and physical gift card issuance, redemption tracking, balance management, and promotional voucher campaigns. Increases cash flow and customer acquisition.

### 17. **Event & Catering Management**
**Priority:** Low  
**Description:**  
Catering order management, event planning tools, equipment tracking, and large party coordination. Expands revenue opportunities beyond regular dining operations.

### 18. **Supplier Management & Procurement**
**Priority:** Low  
**Description:**  
Supplier catalog management, automated purchase order generation, price comparison, and supplier performance tracking. Streamlines procurement process and reduces costs.

### 19. **Multi-Language & Multi-Currency Support**
**Priority:** Low  
**Description:**  
Full system localization with multiple language support for POS, KDS, and customer-facing interfaces. Multi-currency support for international operations. Enables global expansion.

### 20. **API Integration Hub**
**Priority:** Low  
**Description:**  
RESTful API for third-party integrations with accounting software, marketing platforms, delivery services, and payment gateways. Webhook support for real-time event notifications. Enables ecosystem expansion.

---

## Planned Innovations & Roadmap

URY is continuously evolving to incorporate cutting-edge technology and improve user experience. The following innovations are planned for future releases:

### HUF AI Agent Integration
**Status:** Planned  
**Priority:** High  
**Description:**  
Integration with HUF, an advanced AI Agent framework for Frappe systems that supports multiple AI models and provides flexible integration capabilities. This integration will enable intelligent automation across the restaurant management system through multiple interaction modes:

- **Event-Based Automation:** AI agents that react to key operational events (e.g., POS closing, order delays, inventory alerts) with intelligent responses and automated actions
- **Scheduled Intelligence:** Background agents that run on schedule to enforce policies, track metrics, analyze trends, and generate insights
- **Webhook Integration:** AI-powered webhook handlers that process external events and trigger appropriate system responses
- **Chat-Based Assistance:** Conversational AI interface for staff to query data, get recommendations, and perform actions through natural language
- **Smart Functions:** AI-enhanced functions that provide intelligent suggestions, automate decision-making, and optimize operations

This integration will transform URY into an intelligent restaurant management system that learns from operations, predicts needs, and automates routine tasks while maintaining human oversight.

### AI-Powered User Onboarding
**Status:** Planned  
**Priority:** High  
**Description:**  
Revolutionary self-service onboarding system powered by AI that eliminates the need for consultants and technical expertise. The system will guide new restaurant owners through:

- **Intelligent Setup Wizard:** Step-by-step configuration guided by AI that understands restaurant type, size, and operational model
- **Automated Data Import:** AI-assisted data uploading and cleanup that validates, normalizes, and organizes menu items, recipes, pricing, and inventory data
- **Smart Configuration:** AI recommendations for POS settings, printer configurations, room layouts, and operational workflows based on restaurant profile
- **Data Quality Assurance:** Automated data validation, duplicate detection, and cleanup suggestions to ensure accurate setup
- **Contextual Help:** AI-powered help system that provides relevant guidance based on current setup stage and user actions

This innovation will dramatically reduce onboarding time from days/weeks to hours, making URY accessible to restaurants without technical resources or consultant budgets.

### Custom SaaS Frontend Platform
**Status:** Planned  
**Priority:** Medium  
**Description:**  
A fully custom-designed SaaS frontend platform connected to Frappe Cloud infrastructure, providing complete UX ownership and brand control. This platform will offer:

- **Branded Experience:** Fully customizable user interface that reflects restaurant brand identity, colors, and design language
- **Modern UX/UI:** Contemporary design patterns, intuitive navigation, and optimized user flows crafted specifically for restaurant operations
- **Mobile-First Design:** Responsive design optimized for tablets, smartphones, and desktop devices used in restaurant environments
- **Performance Optimization:** Lightweight, fast-loading interface optimized for restaurant operations with offline capability
- **Frappe Cloud Integration:** Seamless backend integration with Frappe Cloud for reliable, scalable infrastructure without managing servers
- **White-Label Capability:** Complete customization options for multi-tenant SaaS deployment with brand-specific experiences

This platform will provide restaurants with a modern, branded experience while leveraging the robust backend infrastructure of Frappe Cloud, combining the best of custom UX design with enterprise-grade reliability.

### Additional Planned Enhancements

#### Intelligent Menu Optimization
AI-powered menu analysis that suggests pricing adjustments, identifies underperforming items, recommends new dishes based on trends, and optimizes menu layout for maximum profitability.

#### Predictive Analytics & Forecasting
Advanced machine learning models that predict daily sales, optimize inventory ordering, forecast staffing needs, and identify seasonal patterns to improve operational efficiency.

#### Voice-Activated Operations
Voice commands for order taking, status updates, and system navigation, enabling hands-free operation in busy kitchen and service environments.

#### Automated Compliance & Reporting
AI agents that automatically generate compliance reports, track regulatory requirements, and ensure adherence to food safety and labor regulations.

#### Smart Inventory Management
AI-powered inventory optimization that predicts ingredient needs, suggests optimal ordering quantities, tracks waste patterns, and automates supplier ordering.

---

## File Tracking

### Files Analyzed

#### Backend (Python/ERPNext)
- `/ury/ury/doctype/` - All doctype definitions (34 doctypes)
- `/ury/ury/report/` - All report definitions (15 reports)
- `/ury/ury/api/` - All API endpoints (10 API files)
- `/ury/ury_pos/api.py` - POS API endpoints
- `/ury/hooks.py` - Application hooks
- `/ury/config/` - Configuration files

#### Frontend Applications
- `/pos/src/` - Modern POS application (React/TypeScript)
- `/urypos/src/` - Legacy POS application (Vue.js)
- `/URYMosaic/src/` - Kitchen Display System (Vue.js)

#### Documentation
- `/README.md` - Project overview
- `/INSTALLATION.md` - Installation guide
- `/SETUP.md` - Setup instructions

### Files Analyzed (Complete)

#### Client-Side Scripts ✅
- ✅ `/ury/public/js/pos_extend.js` - ERPNext POS extensions and customizations
- ✅ `/ury/public/js/pos_print.js` - Invoice printing handlers (QZ, network, browser)
- ✅ `/ury/public/js/quick_entry.js` - Customer quick entry form customization
- ✅ `/ury/public/js/qz-tray.js` - QZ Tray integration library (external)
- ✅ `/ury/public/js/restrict_qty_edit_pos.js` - Quantity edit restrictions
- ✅ `/ury/public/js/sign-message.js` - QZ certificate signing
- ✅ `/ury/public/js/ury_pos_kot.js` - KOT auto-generation on invoice save
- ✅ `/ury/public/js/jsrsasign-all-min.js` - Cryptographic library (external)

#### Doctype Client Scripts ✅
- ✅ All `.js` files in doctype directories analyzed for client-side behaviors

#### Fixtures ✅
- ✅ `/ury/fixtures/custom_field.json` - Custom field definitions (Item add-ons, variants, Branch aggregators, POS Profile extensions)
- ✅ `/ury/fixtures/client_script.json` - Client script configurations
- ✅ `/ury/fixtures/property_setter.json` - Property setters for ERPNext doctypes
- ✅ `/ury/fixtures/custom_html_block.json` - Custom HTML blocks
- ✅ `/ury/fixtures/role.json` - Role definitions

#### ERPNext Extensions ✅
- ✅ `/ury/ury/custom/item.json` - Item doctype customizations (POS variants, add-ons)
- ✅ Customizations to POS Profile, POS Invoice, Branch doctypes

#### Web Pages ✅
- ✅ `/ury/www/pos.py` - POS web page handler and context provider

#### Print Formats ✅
- ✅ `/ury/ury/doctype/ury_daily_p_and_l/profit_loss_details.html` - P&L print template

### Files Pending Review (Optional)
- Test files (for understanding edge cases and validation rules)
- Additional print format templates in ERPNext (if any)

---

## Dependencies Summary

### Core Dependencies
- **ERPNext** (v15) - Base ERP platform providing accounting, inventory, and customer management
- **Frappe Framework** - Web framework and application platform
- **Frappe HR** - Employee management and attendance tracking

### Frontend Dependencies
- **React** (POS v2) - Modern POS interface
- **Vue.js** (POS v1, KDS) - Legacy POS and Kitchen Display System
- **TypeScript** - Type-safe development for POS v2

### Hardware/Software Dependencies
- **CUPS** - Network printer support
- **QZ Tray** - Local printer support (optional)
- **Node.js 18.20+** - Frontend build requirements

---

## Notes

- This documentation is based on code analysis as of the current codebase state
- Some features may have additional configuration options not detailed here
- Integration points with ERPNext are extensive - refer to ERPNext documentation for base functionality
- Frontend applications (POS v2, POS v1, KDS) share backend APIs but have different user interfaces
- Legacy POS (urypos) and KDS (URYMosaic) are maintained for backward compatibility until December 2025
- Planned innovations represent future roadmap items and are subject to change based on development priorities and user feedback

---

*Last Updated: Based on current codebase analysis*  
*For technical implementation details, refer to source code and inline documentation*  
*For roadmap and planned features, see "Planned Innovations & Roadmap" section*
