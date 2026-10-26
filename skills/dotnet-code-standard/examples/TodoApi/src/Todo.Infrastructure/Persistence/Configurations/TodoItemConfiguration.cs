using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Todo.Domain.Todos;

namespace Todo.Infrastructure.Persistence.Configurations;

internal sealed class TodoItemConfiguration : IEntityTypeConfiguration<TodoItem>
{
    public void Configure(EntityTypeBuilder<TodoItem> builder)
    {
        builder.ToTable("todos", table =>
        {
            table.HasCheckConstraint("ck_todos_version_positive", "version >= 1");
        });

        builder.HasKey(todo => todo.Id);
        builder.Property(todo => todo.Id).HasColumnName("id").ValueGeneratedNever();
        builder.Property(todo => todo.OwnerId)
            .HasColumnName("owner_id")
            .HasMaxLength(TodoItem.OwnerIdMaxLength)
            .IsRequired()
            .IsConcurrencyToken();
        builder.Property(todo => todo.Title).HasColumnName("title").HasMaxLength(TodoItem.TitleMaxLength).IsRequired();
        builder.Property(todo => todo.Description).HasColumnName("description").HasMaxLength(TodoItem.DescriptionMaxLength);
        builder.Property(todo => todo.DueDate).HasColumnName("due_date");
        builder.Property(todo => todo.Priority).HasColumnName("priority").HasConversion<string>().HasMaxLength(10);
        builder.Property(todo => todo.Status).HasColumnName("status").HasConversion<string>().HasMaxLength(10);
        builder.Property(todo => todo.CompletedAt).HasColumnName("completed_at");
        builder.Property(todo => todo.Version).HasColumnName("version").IsConcurrencyToken();
        builder.Property(todo => todo.CreatedAt).HasColumnName("created_at");
        builder.Property(todo => todo.UpdatedAt).HasColumnName("updated_at");

        builder.HasIndex(todo => new { todo.OwnerId, todo.Status, todo.CreatedAt, todo.Id })
            .HasDatabaseName("ix_todos_owner_status_created_at");
        builder.HasIndex(todo => new { todo.OwnerId, todo.DueDate, todo.Id }).HasDatabaseName("ix_todos_owner_due_date");
        builder.HasIndex(todo => todo.Title)
            .HasDatabaseName("ix_todos_title_trgm")
            .HasMethod("gin")
            .HasOperators("gin_trgm_ops");
    }
}
