import { beforeEach, describe, expect, it, vi } from 'vitest';

const getDocListMock = vi.fn();

vi.mock('@ury/core', () => ({
  db: {
    getDocList: (...args: unknown[]) => getDocListMock(...args),
  },
}));

import { getActiveTableOrders, getUserFullNames } from './captain-table-api';

describe('getActiveTableOrders', () => {
  beforeEach(() => getDocListMock.mockReset());

  it('queries active invoices for the requested branch with the required fields', async () => {
    getDocListMock.mockResolvedValueOnce([]);

    await getActiveTableOrders('Kozhikode');

    expect(getDocListMock).toHaveBeenCalledWith(
      'POS Invoice',
      expect.objectContaining({
        fields: [
          'name',
          'restaurant_table',
          'custom_merged_tables',
          'waiter',
          'grand_total',
          'invoice_printed',
        ],
        filters: [
          ['branch', '=', 'Kozhikode'],
          ['docstatus', '=', 0],
        ],
      }),
    );
  });

  it('maps primary and merged tables to the same invoice summary', async () => {
    getDocListMock.mockResolvedValueOnce([
      {
        name: 'INV-2',
        restaurant_table: 'T-2',
        custom_merged_tables: 'T-3, T-4',
        waiter: 'waiter@example.com',
        grand_total: 1200,
        invoice_printed: 1,
      },
    ]);

    const result = await getActiveTableOrders('Kozhikode');
    const expected = {
      invoiceName: 'INV-2',
      waiter: 'waiter@example.com',
      grandTotal: 1200,
      invoicePrinted: true,
    };

    expect(result.size).toBe(3);
    expect(result.get('T-2')).toEqual(expected);
    expect(result.get('T-3')).toEqual(expected);
    expect(result.get('T-4')).toEqual(expected);
  });

  it('skips invoices without a restaurant table', async () => {
    getDocListMock.mockResolvedValueOnce([
      {
        name: 'INV-3',
        restaurant_table: null,
        custom_merged_tables: null,
        waiter: 'waiter@example.com',
        grand_total: 300,
        invoice_printed: 0,
      },
    ]);

    expect((await getActiveTableOrders('Kozhikode')).size).toBe(0);
  });

  it('returns an empty map when there are no active invoices', async () => {
    getDocListMock.mockResolvedValueOnce([]);
    expect((await getActiveTableOrders('Kozhikode')).size).toBe(0);
  });
});

describe('getUserFullNames', () => {
  beforeEach(() => getDocListMock.mockReset());

  it('does not query when there are no user names', async () => {
    expect(await getUserFullNames([])).toEqual(new Map());
    expect(getDocListMock).not.toHaveBeenCalled();
  });

  it('filters falsy values and de-duplicates user names before querying', async () => {
    getDocListMock.mockResolvedValueOnce([]);

    await getUserFullNames(['a@example.com', '', 'a@example.com', 'b@example.com']);

    expect(getDocListMock).toHaveBeenCalledWith(
      'User',
      expect.objectContaining({
        filters: [['name', 'in', ['a@example.com', 'b@example.com']]],
        limit: 2,
      }),
    );
  });

  it('maps full names and falls back to the user id', async () => {
    getDocListMock.mockResolvedValueOnce([
      { name: 'a@example.com', full_name: 'Alice A' },
      { name: 'b@example.com', full_name: '' },
    ]);

    const result = await getUserFullNames(['a@example.com', 'b@example.com']);
    expect(result.get('a@example.com')).toBe('Alice A');
    expect(result.get('b@example.com')).toBe('b@example.com');
  });
});
