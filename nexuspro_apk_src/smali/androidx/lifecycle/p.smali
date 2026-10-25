.class public final synthetic Landroidx/lifecycle/p;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Ljava/lang/Runnable;


# instance fields
.field public final synthetic a:Landroidx/lifecycle/q;


# direct methods
.method public synthetic constructor <init>(Landroidx/lifecycle/q;)V
    .locals 0

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, Landroidx/lifecycle/p;->a:Landroidx/lifecycle/q;

    return-void
.end method


# virtual methods
.method public final run()V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/lifecycle/p;->a:Landroidx/lifecycle/q;

    invoke-static {v0}, Landroidx/lifecycle/q;->b(Landroidx/lifecycle/q;)V

    return-void
.end method
