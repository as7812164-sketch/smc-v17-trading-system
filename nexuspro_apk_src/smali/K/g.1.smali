.class public final synthetic LK/g;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Ljava/lang/Runnable;


# instance fields
.field public final synthetic a:LK/h;


# direct methods
.method public synthetic constructor <init>(LK/h;)V
    .locals 0

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, LK/g;->a:LK/h;

    return-void
.end method


# virtual methods
.method public final run()V
    .locals 1

    .line 1
    iget-object v0, p0, LK/g;->a:LK/h;

    invoke-static {v0}, LK/h;->a(LK/h;)V

    return-void
.end method
