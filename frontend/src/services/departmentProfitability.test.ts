import { beforeEach, describe, expect, it, vi } from 'vitest';
import { call } from '@ury/core';
import { departmentProfitabilityService } from './departmentProfitability';

vi.mock('@ury/core', () => ({
  call: vi.fn(),
}));

const mockedCall = vi.mocked(call);

describe('departmentProfitabilityService', () => {
  beforeEach(() => {
    mockedCall.mockReset();
  });

  it('calls the profitability endpoint with the provided filters and unwraps message payloads', async () => {
    const result = {
      company: 'URY',
      branch: 'Kozhikode',
      service_date_or_period: '2026-09-17',
      department: 'Hot Kitchen',
      rows: [
        {
          company: 'URY',
          branch: 'Kozhikode',
          service_date_or_period: '2026-09-17',
          department: 'Hot Kitchen',
          item_or_component: 'Chicken Biryani',
          source_document: 'SINV-0001',
          net_revenue: 2500,
          posted_cost: 1400,
          theoretical_cost: 1300,
          posted_gross_profit: 1100,
          theoretical_gross_profit: 1200,
          variance: 100,
        },
      ],
    };
    mockedCall.mockResolvedValueOnce({ message: result });

    await expect(
      departmentProfitabilityService.getDepartmentProfitability({
        company: 'URY',
        branch: 'Kozhikode',
        service_date_or_period: '2026-09-17',
        department: 'Hot Kitchen',
      })
    ).resolves.toBe(result);

    expect(mockedCall).toHaveBeenCalledWith(
      'ury.ury.api.ury_department_profitability.get_department_profitability',
      {
        company: 'URY',
        branch: 'Kozhikode',
        service_date_or_period: '2026-09-17',
        department: 'Hot Kitchen',
      }
    );
  });

  it('preserves omitted optional department filters when requesting profitability', async () => {
    const result = {
      company: 'URY',
      branch: 'Kozhikode',
      service_date_or_period: '2026-09',
      rows: [],
      reason: 'MISSING_APPROVED_PLAN',
      provisional: true,
    };
    mockedCall.mockResolvedValueOnce(result);

    await expect(
      departmentProfitabilityService.getDepartmentProfitability({
        company: 'URY',
        branch: 'Kozhikode',
        service_date_or_period: '2026-09',
      })
    ).resolves.toBe(result);

    expect(mockedCall).toHaveBeenCalledWith(
      'ury.ury.api.ury_department_profitability.get_department_profitability',
      {
        company: 'URY',
        branch: 'Kozhikode',
        service_date_or_period: '2026-09',
        department: undefined,
      }
    );
  });

  it('calls the plan-vs-actual endpoint and unwraps message payloads', async () => {
    const result = {
      company: 'URY',
      branch: 'Kozhikode',
      service_date_or_period: '2026-09-17',
      department: 'Hot Kitchen',
      rows: [
        {
          company: 'URY',
          branch: 'Kozhikode',
          service_date_or_period: '2026-09-17',
          department: 'Hot Kitchen',
          item_or_component: 'Chicken Biryani',
          source_document: 'SINV-0001',
          planned_qty: 120,
          actual_qty: 115,
          qty_variance: -5,
        },
      ],
    };
    mockedCall.mockResolvedValueOnce({ message: result });

    await expect(
      departmentProfitabilityService.getPlanVsActual({
        company: 'URY',
        branch: 'Kozhikode',
        service_date_or_period: '2026-09-17',
        department: 'Hot Kitchen',
      })
    ).resolves.toBe(result);

    expect(mockedCall).toHaveBeenCalledWith(
      'ury.ury.api.ury_department_profitability.get_plan_vs_actual',
      {
        company: 'URY',
        branch: 'Kozhikode',
        service_date_or_period: '2026-09-17',
        department: 'Hot Kitchen',
      }
    );
  });
});
