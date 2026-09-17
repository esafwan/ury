import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getTableOrderContextMock = vi.fn();

vi.mock('../../lib/table-order-context-api', () => ({
  getTableOrderContext: (...args: unknown[]) => getTableOrderContextMock(...args),
}));

const setSelectedTableMock = vi.fn();
const clearTableOrderMock = vi.fn();

let storeState = {
  orderLoading: false,
  activeOrders: [] as OrderItem[],
  setSelectedTable: setSelectedTableMock,
  clearTableOrder: clearTableOrderMock,
};

vi.mock('../../store/pos-store', () => ({
  usePOSStore: (selector: (state: typeof storeState) => unknown) => selector(storeState),
}));

import { useTableOrderContext } from './useTableOrderContext';
import type { TableOrderContext } from '../../lib/table-order-context-api';
import type { OrderItem } from '../../store/pos-store';

const buildContext = (overrides: Partial<TableOrderContext> = {}): TableOrderContext => ({
  table: { name: 'T-1', branch: 'Kozhikode', restaurant_room: 'Main Hall' },
  order: null,
  assignment: null,
  permissions: {
    view: true,
    modify: true,
    reduce_items: true,
    remove_items: true,
    transfer_table: true,
    transfer_captain: true,
    print_bill: true,
    reprint_kot: true,
    settle: true,
    cancel: true,
  },
  ...overrides,
});

const buildOrderItem = (overrides: Record<string, unknown> = {}) =>
  ({
    uniqueId: 'u1',
    id: 'ITEM-1',
    name: 'Item 1',
    price: 100,
    quantity: 2,
    comment: undefined,
    ...overrides,
  }) as unknown as OrderItem;

describe('useTableOrderContext', () => {
  beforeEach(() => {
    getTableOrderContextMock.mockReset();
    setSelectedTableMock.mockClear();
    clearTableOrderMock.mockClear();
    storeState = {
      orderLoading: false,
      activeOrders: [],
      setSelectedTable: setSelectedTableMock,
      clearTableOrder: clearTableOrderMock,
    };
  });

  it('does not fetch when no table is selected', () => {
    const { result } = renderHook(() => useTableOrderContext(undefined));

    expect(getTableOrderContextMock).not.toHaveBeenCalled();
    expect(result.current.isContextLoading).toBe(true);
    expect(result.current.context).toBeNull();
    expect(result.current.isOrderReady).toBe(false);
  });

  it('fetches context and wires a viewable table into the POS store', async () => {
    const context = buildContext();
    getTableOrderContextMock.mockResolvedValueOnce(context);

    const { result } = renderHook(() => useTableOrderContext('T-1'));
    await waitFor(() => expect(result.current.isContextLoading).toBe(false));

    expect(getTableOrderContextMock).toHaveBeenCalledWith('T-1');
    expect(result.current.context).toEqual(context);
    expect(result.current.permissions).toEqual(context.permissions);
    expect(setSelectedTableMock).toHaveBeenCalledWith('T-1', 'Main Hall');
  });

  it('does not wire a table when view permission is denied', async () => {
    getTableOrderContextMock.mockResolvedValueOnce(
      buildContext({ permissions: { ...buildContext().permissions, view: false } }),
    );

    const { result } = renderHook(() => useTableOrderContext('T-1'));
    await waitFor(() => expect(result.current.isContextLoading).toBe(false));

    expect(setSelectedTableMock).not.toHaveBeenCalled();
  });

  it('surfaces context errors and keeps the context empty', async () => {
    getTableOrderContextMock.mockRejectedValueOnce(new Error('403 Forbidden'));

    const { result } = renderHook(() => useTableOrderContext('T-1'));
    await waitFor(() => expect(result.current.isContextLoading).toBe(false));

    expect(result.current.contextError).toBe('403 Forbidden');
    expect(result.current.context).toBeNull();
    expect(setSelectedTableMock).not.toHaveBeenCalled();
  });

  it('uses a generic message for non-Error rejections', async () => {
    getTableOrderContextMock.mockRejectedValueOnce({});

    const { result } = renderHook(() => useTableOrderContext('T-1'));
    await waitFor(() => expect(result.current.isContextLoading).toBe(false));

    expect(result.current.contextError).toBe('Failed to load table order context.');
  });

  it('captures the loaded baseline and groups increases, additions, and reductions', async () => {
    storeState.orderLoading = true;
    getTableOrderContextMock.mockResolvedValueOnce(buildContext());

    const { result, rerender } = renderHook(() => useTableOrderContext('T-1'));
    await waitFor(() => expect(result.current.context).not.toBeNull());

    storeState.activeOrders = [buildOrderItem({ quantity: 2 })];
    storeState.orderLoading = false;
    rerender();
    await waitFor(() => expect(result.current.isOrderReady).toBe(true));

    expect(result.current.alreadyOrderedLines).toHaveLength(1);
    expect(result.current.alreadyOrderedLines[0]).toMatchObject({
      uniqueId: 'u1',
      baseQty: 2,
      curQty: 2,
      delta: 0,
      confirmedQty: 2,
    });

    storeState.activeOrders = [
      buildOrderItem({ quantity: 3 }),
      buildOrderItem({ uniqueId: 'u2', id: 'ITEM-2', name: 'Item 2', quantity: 1 }),
    ];
    rerender();
    await waitFor(() => expect(result.current.newOrChangedLines).toHaveLength(2));

    expect(result.current.newOrChangedLines).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ uniqueId: 'u1', baseQty: 2, curQty: 3, delta: 1 }),
        expect.objectContaining({ uniqueId: 'u2', baseQty: 0, curQty: 1, delta: 1 }),
      ]),
    );

    storeState.activeOrders = [buildOrderItem({ quantity: 0 })];
    rerender();
    await waitFor(() => expect(result.current.reductionPendingLines).toHaveLength(1));
    expect(result.current.reductionPendingLines[0]).toMatchObject({
      baseQty: 2,
      curQty: 0,
      delta: -2,
      confirmedQty: 0,
    });
    expect(result.current.alreadyOrderedLines).toHaveLength(0);
  });

  it('refetches context without rewiring the POS store', async () => {
    getTableOrderContextMock.mockResolvedValueOnce(buildContext());
    const { result } = renderHook(() => useTableOrderContext('T-1'));
    await waitFor(() => expect(result.current.isContextLoading).toBe(false));

    setSelectedTableMock.mockClear();
    getTableOrderContextMock.mockResolvedValueOnce(buildContext({ order: null }));
    await act(async () => result.current.refetchContext());

    expect(getTableOrderContextMock).toHaveBeenCalledTimes(2);
    expect(setSelectedTableMock).not.toHaveBeenCalled();
  });

  it('clears the table order when the hook unmounts', async () => {
    getTableOrderContextMock.mockResolvedValueOnce(buildContext());
    const { result, unmount } = renderHook(() => useTableOrderContext('T-1'));
    await waitFor(() => expect(result.current.isContextLoading).toBe(false));

    unmount();
    expect(clearTableOrderMock).toHaveBeenCalled();
  });
});
