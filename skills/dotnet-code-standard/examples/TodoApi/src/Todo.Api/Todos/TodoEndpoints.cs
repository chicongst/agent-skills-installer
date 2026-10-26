using System.Security.Claims;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Mvc;
using Todo.Api.Auth;
using Todo.Api.Http;
using Todo.Application.Todos.CompleteTodo;
using Todo.Application.Todos.CreateTodo;
using Todo.Application.Todos.DeleteTodo;
using Todo.Application.Todos.GetTodo;
using Todo.Application.Todos.ListTodos;
using Todo.Application.Todos.ReopenTodo;
using Todo.Application.Todos.UpdateTodo;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Api.Todos;

internal static class TodoEndpoints
{
    public static IEndpointRouteBuilder MapTodoEndpoints(this IEndpointRouteBuilder app)
    {
        var todos = app.MapGroup("/todos").WithTags("Todos").RequireAuthorization();

        todos.MapGet("/", ListAsync).WithName("ListTodos");
        todos.MapGet("/{id:guid}", GetAsync).WithName("GetTodo");

        var writes = todos.MapGroup("/").RequireRateLimiting(RateLimitPolicies.Writes);
        writes.MapPost("/", CreateAsync).WithName("CreateTodo");
        writes.MapPatch("/{id:guid}", UpdateAsync).WithName("UpdateTodo");
        writes.MapPost("/{id:guid}/complete", CompleteAsync).WithName("CompleteTodo");
        writes.MapPost("/{id:guid}/reopen", ReopenAsync).WithName("ReopenTodo");
        writes.MapDelete("/{id:guid}", DeleteAsync).WithName("DeleteTodo");

        return app;
    }

    private static async Task<Results<Created<TodoResponse>, ProblemHttpResult>> CreateAsync(
        CreateTodoRequest request,
        ClaimsPrincipal user,
        CreateTodoHandler handler,
        HttpResponse response,
        CancellationToken cancellationToken)
    {
        var result = await handler.HandleAsync(new CreateTodoCommand(user.GetOwnerId(), request.ToDraft()), cancellationToken);
        if (!result.IsSuccess)
        {
            return Problems.From(result.Error);
        }

        response.Headers.ETag = ETag.From(result.Value.Version);
        return TypedResults.Created($"/todos/{result.Value.Id}", TodoResponse.From(result.Value));
    }

    private static async Task<Results<Ok<TodoPageResponse>, ProblemHttpResult>> ListAsync(
        [AsParameters] ListTodosParameters parameters,
        ClaimsPrincipal user,
        ListTodosHandler handler,
        CancellationToken cancellationToken)
    {
        var query = TodoListQueryParser.Parse(user.GetOwnerId(), parameters);
        if (!query.IsSuccess)
        {
            return Problems.From(query.Error);
        }

        var page = await handler.HandleAsync(query.Value, cancellationToken);
        return page.IsSuccess ? TypedResults.Ok(TodoPageResponse.From(page.Value)) : Problems.From(page.Error);
    }

    private static async Task<Results<Ok<TodoResponse>, ProblemHttpResult>> GetAsync(
        Guid id,
        ClaimsPrincipal user,
        GetTodoHandler handler,
        HttpResponse response,
        CancellationToken cancellationToken) =>
        ToOk(await handler.HandleAsync(new GetTodoQuery(user.GetOwnerId(), id), cancellationToken), response);

    private static Task<Results<Ok<TodoResponse>, ProblemHttpResult>> UpdateAsync(
        Guid id,
        UpdateTodoRequest request,
        [FromHeader(Name = "If-Match")] string? ifMatch,
        ClaimsPrincipal user,
        UpdateTodoHandler handler,
        HttpResponse response,
        CancellationToken cancellationToken) =>
        WriteAsync(ifMatch, response, version => handler.HandleAsync(
            new UpdateTodoCommand(user.GetOwnerId(), id, version, request.ToChanges()),
            cancellationToken));

    private static Task<Results<Ok<TodoResponse>, ProblemHttpResult>> CompleteAsync(
        Guid id,
        [FromHeader(Name = "If-Match")] string? ifMatch,
        ClaimsPrincipal user,
        CompleteTodoHandler handler,
        HttpResponse response,
        CancellationToken cancellationToken) =>
        WriteAsync(ifMatch, response, version => handler.HandleAsync(
            new CompleteTodoCommand(user.GetOwnerId(), id, version),
            cancellationToken));

    private static Task<Results<Ok<TodoResponse>, ProblemHttpResult>> ReopenAsync(
        Guid id,
        [FromHeader(Name = "If-Match")] string? ifMatch,
        ClaimsPrincipal user,
        ReopenTodoHandler handler,
        HttpResponse response,
        CancellationToken cancellationToken) =>
        WriteAsync(ifMatch, response, version => handler.HandleAsync(
            new ReopenTodoCommand(user.GetOwnerId(), id, version),
            cancellationToken));

    private static async Task<Results<NoContent, ProblemHttpResult>> DeleteAsync(
        Guid id,
        [FromHeader(Name = "If-Match")] string? ifMatch,
        ClaimsPrincipal user,
        DeleteTodoHandler handler,
        CancellationToken cancellationToken)
    {
        var expected = ETag.Parse(ifMatch);
        if (expected.State != IfMatchState.Valid)
        {
            return Problems.For(expected);
        }

        var error = await handler.HandleAsync(new DeleteTodoCommand(user.GetOwnerId(), id, expected.Version), cancellationToken);
        return error is null ? TypedResults.NoContent() : Problems.From(error);
    }

    private static async Task<Results<Ok<TodoResponse>, ProblemHttpResult>> WriteAsync(
        string? ifMatch,
        HttpResponse response,
        Func<int, Task<Result<TodoItem>>> write)
    {
        var expected = ETag.Parse(ifMatch);
        if (expected.State != IfMatchState.Valid)
        {
            return Problems.For(expected);
        }

        return ToOk(await write(expected.Version), response);
    }

    private static Results<Ok<TodoResponse>, ProblemHttpResult> ToOk(Result<TodoItem> result, HttpResponse response)
    {
        if (!result.IsSuccess)
        {
            return Problems.From(result.Error);
        }

        response.Headers.ETag = ETag.From(result.Value.Version);
        return TypedResults.Ok(TodoResponse.From(result.Value));
    }
}
