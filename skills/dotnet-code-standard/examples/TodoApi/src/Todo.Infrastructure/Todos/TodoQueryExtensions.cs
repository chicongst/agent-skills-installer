using Todo.Application.Abstractions;
using Todo.Domain.Todos;

namespace Todo.Infrastructure.Todos;

internal static class TodoQueryExtensions
{
    public static IOrderedQueryable<TodoItem> SortBy(this IQueryable<TodoItem> todos, TodoSort sort) =>
        (sort.Field, sort.Descending) switch
        {
            (TodoSortField.DueDate, false) => todos.OrderBy(t => t.DueDate == null).ThenBy(t => t.DueDate).ThenBy(t => t.Id),
            (TodoSortField.DueDate, true) => todos.OrderBy(t => t.DueDate == null).ThenByDescending(t => t.DueDate).ThenBy(t => t.Id),
            (TodoSortField.CreatedAt, false) => todos.OrderBy(t => t.CreatedAt).ThenBy(t => t.Id),
            _ => todos.OrderByDescending(t => t.CreatedAt).ThenBy(t => t.Id),
        };
}
