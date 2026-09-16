import { beforeEach, describe, expect, it, vi } from 'vitest';
import { call } from '@ury/core';
import { departmentStockService } from './departmentStock';

vi.mock('@ury/core', () => {
  const mockedCall = vi.fn();
  return {
    call: Object.assign(mockedCall, {
      get: vi.fn(),
    }),
  };
});

const mockedCall = vi.mocked(call);
const mockedCallGet = vi.mocked(call.get);

describe('departmentStockService', () => {
  beforeEach(() => {
    mockedCall.mockReset();
    mockedCallGet.mockReset();
  });

  it('lists enabled production departments for a concrete branch', async () => {
    mockedCall.mockResolvedValueOnce({
      message: [
        { name: 'Hot Kitchen', department_name: 'Hot Kitchen Display' },
        { name: 'Bakery' },
      ],
    });

    await expect(departmentStockService.listDepartments('Kozhikode')).resolves.toEqual([
      { name: 'Hot Kitchen', department_name: 'Hot Kitchen Display' },
      { name: 'Bakery', department_name: 'Bakery' },
    ]);

    expect(mockedCall).toHaveBeenCalledWith('frappe.client.get_list', {
      doctype: 'URY Production Department',
      filters: { branch: 'Kozhikode', enabled: 1 },
      fields: ['name', 'department_name'],
      limit_page_length: 0,
    });
  });

  it('does not call the backend when department branch scope is missing or all', async () => {
    await expect(departmentStockService.listDepartments('')).resolves.toEqual([]);
    await expect(departmentStockService.listDepartments('all')).resolves.toEqual([]);

    expect(mockedCall).not.toHaveBeenCalled();
  });

  it('lists issue authorizations with all-branch scope normalized and numeric fields coerced', async () => {
    mockedCall.mockResolvedValueOnce({
      message: [
        {
          name: 'AUTH-1',
          plan: 'PLAN-1',
          department: 'Hot Kitchen',
          component_item: 'ITEM-1',
          status: 'Authorized',
          required_qty: '12.5',
          authorized_qty: '10',
          remaining_after_qty: null,
          stock_uom: 'Nos',
        },
      ],
    });

    await expect(
      departmentStockService.listIssueAuthorizations({
        branch: 'all',
        company: 'URY',
        department: 'Hot Kitchen',
        from_date: '2026-09-01',
        to_date: '2026-09-17',
      })
    ).resolves.toEqual([
      {
        name: 'AUTH-1',
        plan: 'PLAN-1',
        department: 'Hot Kitchen',
        component_item: 'ITEM-1',
        component_item_name: undefined,
        branch: undefined,
        company: undefined,
        production_unit: undefined,
        status: 'Authorized',
        required_qty: 12.5,
        authorized_qty: 10,
        remaining_after_qty: 0,
        stock_uom: 'Nos',
        creation: undefined,
      },
    ]);

    expect(mockedCall).toHaveBeenCalledWith('ury.ury.api.ury_issue_authorization.list_issue_authorizations', {
      branch: undefined,
      company: 'URY',
      department: 'Hot Kitchen',
      from_date: '2026-09-01',
      to_date: '2026-09-17',
    });
  });

  it('lists stock movements and falls back to an empty array for non-list payloads', async () => {
    mockedCall.mockResolvedValueOnce({ message: { rows: [] } });

    await expect(
      departmentStockService.listStockMovements({
        branch: 'Kozhikode',
        company: 'URY',
        department: 'Hot Kitchen',
        from_date: '2026-09-01',
        to_date: '2026-09-17',
      })
    ).resolves.toEqual([]);

    expect(mockedCall).toHaveBeenCalledWith('ury.ury.api.ury_stock_service.list_stock_movements', {
      branch: 'Kozhikode',
      company: 'URY',
      department: 'Hot Kitchen',
      from_date: '2026-09-01',
      to_date: '2026-09-17',
    });
  });

  it('normalizes wastage rows and drops blank optional text fields', async () => {
    mockedCall.mockResolvedValueOnce({
      message: [
        {
          name: 'WASTE-1',
          component_item: 'ITEM-1',
          wasted_qty: '2.25',
          status: 'Draft',
          department: 'Hot Kitchen',
          valuation_rate: '15',
          valuation_amount: '33.75',
          reason_category: '',
          reason_notes: '',
          captured_by: '',
          captured_on: '',
        },
      ],
    });

    await expect(
      departmentStockService.listWastage({
        branch: 'Kozhikode',
        company: 'URY',
        department: 'Hot Kitchen',
        from_date: '2026-09-01',
        to_date: '2026-09-17',
      })
    ).resolves.toEqual([
      {
        name: 'WASTE-1',
        component_item: 'ITEM-1',
        wasted_qty: 2.25,
        status: 'Draft',
        department: 'Hot Kitchen',
        branch: undefined,
        company: undefined,
        valuation_rate: 15,
        valuation_amount: 33.75,
        reason_category: undefined,
        reason_notes: undefined,
        captured_by: undefined,
        captured_on: undefined,
        approved_by: undefined,
        approved_on: undefined,
      },
    ]);
  });

  it('calls wastage mutation endpoints and unwraps returned rows', async () => {
    mockedCall
      .mockResolvedValueOnce({ message: { name: 'WASTE-1', component_item: 'ITEM-1', wasted_qty: '1', status: 'Draft', department: 'Hot Kitchen' } })
      .mockResolvedValueOnce({ message: { name: 'WASTE-1', component_item: 'ITEM-1', wasted_qty: '1', status: 'Authorized', department: 'Hot Kitchen' } })
      .mockResolvedValueOnce({ name: 'WASTE-2', component_item: 'ITEM-2', wasted_qty: '2', status: 'Rejected', department: 'Bakery' });

    await expect(
      departmentStockService.captureWastage({
        issue_authorization: 'AUTH-1',
        wasted_qty: 1,
        reason_category: 'Spoilage',
        reason_notes: 'Spilled',
        branch: 'Kozhikode',
        company: 'URY',
      })
    ).resolves.toMatchObject({ name: 'WASTE-1', wasted_qty: 1, status: 'Draft' });
    await expect(departmentStockService.approveWastage('WASTE-1')).resolves.toMatchObject({ status: 'Authorized' });
    await expect(departmentStockService.rejectWastage('WASTE-2')).resolves.toMatchObject({ status: 'Rejected', wasted_qty: 2 });

    expect(mockedCall).toHaveBeenNthCalledWith(1, 'ury.ury.api.ury_wastage.capture_wastage', {
      issue_authorization: 'AUTH-1',
      wasted_qty: 1,
      reason_category: 'Spoilage',
      reason_notes: 'Spilled',
      branch: 'Kozhikode',
      company: 'URY',
    });
    expect(mockedCall).toHaveBeenNthCalledWith(2, 'ury.ury.api.ury_wastage.approve_wastage', { wastage: 'WASTE-1' });
    expect(mockedCall).toHaveBeenNthCalledWith(3, 'ury.ury.api.ury_wastage.reject_wastage', { wastage: 'WASTE-2' });
  });

  it('loads an active plan and parses demand vector snapshots', async () => {
    mockedCallGet
      .mockResolvedValueOnce({ message: { name: 'PLAN-1', status: 'Approved' } })
      .mockResolvedValueOnce({
        message: {
          name: 'PLAN-1',
          status: 'Locked',
          approval_snapshot: JSON.stringify({
            demand_vector: [
              {
                component_item: 'ITEM-1',
                department: 'Hot Kitchen',
                required_qty: 12,
              },
            ],
          }),
        },
      });

    await expect(departmentStockService.getActivePlan('Kozhikode', '2026-09-17')).resolves.toEqual({
      name: 'PLAN-1',
      status: 'Locked',
      demandVector: [{ component_item: 'ITEM-1', department: 'Hot Kitchen', required_qty: 12 }],
    });

    expect(mockedCallGet).toHaveBeenNthCalledWith(1, 'ury.ury.api.ury_sales_plan.get_plan_status', {
      branch: 'Kozhikode',
      plan_date: '2026-09-17',
    });
    expect(mockedCallGet).toHaveBeenNthCalledWith(2, 'ury.ury.api.ury_sales_plan.get_plan', { name: 'PLAN-1' });
  });

  it('returns no active plan without a valid scope, plan name, or parseable snapshot', async () => {
    await expect(departmentStockService.getActivePlan('all', '2026-09-17')).resolves.toBeNull();
    expect(mockedCallGet).not.toHaveBeenCalled();

    mockedCallGet.mockResolvedValueOnce({ message: { status: 'Draft' } });
    await expect(departmentStockService.getActivePlan('Kozhikode', '2026-09-17')).resolves.toBeNull();

    mockedCallGet
      .mockResolvedValueOnce({ message: { name: 'PLAN-1', status: 'Approved' } })
      .mockResolvedValueOnce({ message: { name: 'PLAN-1', approval_snapshot: '{' } });
    await expect(departmentStockService.getActivePlan('Kozhikode', '2026-09-17')).resolves.toEqual({
      name: 'PLAN-1',
      status: 'Approved',
      demandVector: [],
    });
  });

  it('creates issue authorizations and records yield checks through the expected endpoints', async () => {
    mockedCall
      .mockResolvedValueOnce({
        message: {
          name: 'AUTH-1',
          plan: 'PLAN-1',
          department: 'Hot Kitchen',
          component_item: 'ITEM-1',
          status: 'Draft',
          required_qty: '0',
          authorized_qty: '5',
          remaining_after_qty: '5',
        },
      })
      .mockResolvedValueOnce({ message: { name: 'YIELD-1', item: 'ITEM-1', branch: 'Kozhikode', company: 'URY', check_type: 'Daily' } });

    await expect(
      departmentStockService.createIssueAuthorization({
        plan: 'PLAN-1',
        department: 'Hot Kitchen',
        component_item: 'ITEM-1',
        requested_qty: 5,
        branch: 'Kozhikode',
        company: 'URY',
        production_unit: 'Main Kitchen',
      })
    ).resolves.toMatchObject({ name: 'AUTH-1', authorized_qty: 5 });

    await expect(
      departmentStockService.recordYieldCheck({
        item: 'ITEM-1',
        branch: 'Kozhikode',
        company: 'URY',
        input_qty: 10,
        output_qty: 8,
        stock_uom: 'Nos',
        check_type: 'Daily',
        issue_authorization: 'AUTH-1',
        department: 'Hot Kitchen',
        production_unit: 'Main Kitchen',
      })
    ).resolves.toEqual({ name: 'YIELD-1', item: 'ITEM-1', branch: 'Kozhikode', company: 'URY', check_type: 'Daily' });

    expect(mockedCall).toHaveBeenNthCalledWith(1, 'ury.ury.api.ury_issue_authorization.create_issue_authorization', {
      plan: 'PLAN-1',
      department: 'Hot Kitchen',
      component_item: 'ITEM-1',
      requested_qty: 5,
      branch: 'Kozhikode',
      company: 'URY',
      production_unit: 'Main Kitchen',
    });
    expect(mockedCall).toHaveBeenNthCalledWith(2, 'ury.ury.api.ury_yield_variance.record_yield_check', {
      item: 'ITEM-1',
      branch: 'Kozhikode',
      company: 'URY',
      input_qty: 10,
      output_qty: 8,
      stock_uom: 'Nos',
      check_type: 'Daily',
      issue_authorization: 'AUTH-1',
      department: 'Hot Kitchen',
      production_unit: 'Main Kitchen',
    });
  });

  it('gets plan stock on hand only when branch and items are provided', async () => {
    await expect(departmentStockService.getPlanStockOnHand('all', [{ item_code: 'ITEM-1' }])).resolves.toEqual([]);
    await expect(departmentStockService.getPlanStockOnHand('Kozhikode', [])).resolves.toEqual([]);
    expect(mockedCallGet).not.toHaveBeenCalled();

    mockedCallGet.mockResolvedValueOnce({
      message: [
        {
          item_code: 'ITEM-1',
          department: 'Hot Kitchen',
          actual_qty: 4,
          resolved_from: 'department',
        },
      ],
    });

    await expect(
      departmentStockService.getPlanStockOnHand('Kozhikode', [{ item_code: 'ITEM-1', department: 'Hot Kitchen' }])
    ).resolves.toEqual([{ item_code: 'ITEM-1', department: 'Hot Kitchen', actual_qty: 4, resolved_from: 'department' }]);

    expect(mockedCallGet).toHaveBeenCalledWith('ury.ury.api.ury_requirements_stock.get_plan_stock_on_hand', {
      branch: 'Kozhikode',
      items: JSON.stringify([{ item_code: 'ITEM-1', department: 'Hot Kitchen' }]),
    });

    mockedCallGet.mockResolvedValueOnce({ message: { rows: [] } });
    await expect(departmentStockService.getPlanStockOnHand('Kozhikode', [{ item_code: 'ITEM-2' }])).resolves.toEqual([]);
  });
});
